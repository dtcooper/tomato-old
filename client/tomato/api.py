from collections import defaultdict
import datetime
import logging
from json.decoder import JSONDecodeError
import os
import random
import time

from django.core.serializers import deserialize
from django.db import transaction
import requests

from . import constants
from .constants import APIException
from .config import Config
from .models import Asset, Rotator, StopSet, StopSetRotator

logger = logging.getLogger('tomato')


class make_request:
    def __init__(self):
        self.conf = Config()

    def __call__(self, method, endpoint, **params):
        headers = {'User-Agent': constants.REQUEST_USER_AGENT}
        if self.conf.auth_token:
            headers['X-Auth-Token'] = self.conf.auth_token

        url = f'{self.conf.protocol}://{self.conf.hostname}/{endpoint}'
        logger.info(f'Hitting [{method.upper()}] {url}')
        try:
            response = requests.request(method, url, headers=headers,
                                        timeout=constants.REQUEST_TIMEOUT, **params)
        except Exception as e:
            if isinstance(e, requests.exceptions.Timeout):
                error = constants.API_ERROR_REQUESTS_TIMEOUT
            else:
                error = constants.API_ERROR_REQUESTS_ERROR
                logger.exception('Requests library threw an exception')
            raise APIException(error)

        else:
            if response.status_code == 200:
                try:
                    return response.json()
                except JSONDecodeError:
                    raise APIException(constants.API_ERROR_JSON_DECODE_ERROR)
            else:
                error = (constants.API_ERROR_ACCESS_DENIED if response.status_code == 403
                         else constants.API_ERROR_INVALID_HTTP_STATUS_CODE)
                raise APIException(error)


make_request = make_request()


class APIBase:
    def __init__(self, cef_window):
        self.conf = cef_window.conf
        self.cef_window = cef_window
        self._execute_js_func = self.cef_window.browser.ExecuteFunction


class AuthAPI(APIBase):
    namespace = 'auth'

    def logout(self):
        self.conf.update(auth_token=None, last_sync=None)

        # TODO: When is the best time clean up assets? We shouldn't do it on sync
        # because old assets may be being streamed from in CEF window.

        # Clean up unused assets on logout
        db_asset_paths = {asset.audio.path for asset in Asset.objects.all()}
        for dirpath, dirnames, filenames in os.walk(constants.MEDIA_DIR):
            for filename in filenames:
                asset_path = os.path.join(dirpath, filename)
                if asset_path not in db_asset_paths:
                    logger.info(f'sync: Removing unused asset: {asset_path}')
                    os.remove(asset_path)

    def check_authorization(self):
        logged_in = connected = False

        if self.conf.protocol and self.conf.hostname and self.conf.auth_token:
            try:
                response = make_request('get', 'ping')
            except APIException as e:
                if str(e) in (constants.API_ERROR_REQUESTS_TIMEOUT, constants.API_ERROR_REQUESTS_ERROR):
                    # If requests failed, we're logged in but not connected
                    logged_in = True
                else:
                    raise
            else:
                connected = True
                logged_in = response['valid_token']

        return (logged_in, connected, bool(self.conf.last_sync))

    def login(self, protocol, hostname, username, password):
        if not hostname:
            raise APIException(constants.API_ERROR_NO_HOSTNAME)

        self.conf.update(hostname=hostname, protocol=protocol)

        if not username or not password:
            raise APIException(constants.API_ERROR_NO_USERPASS)

        response = make_request('post', 'auth', data={'username': username, 'password': password})
        self.conf.auth_token = response.get('auth_token')


class ConfigAPI(APIBase):
    namespace = 'writeconf'

    def set(self, attr, value):
        setattr(self.conf, attr, value)

    def update(self, kwargs):
        self.conf.update(**kwargs)


class ModelsAPI(APIBase):
    namespace = 'models'

    @staticmethod
    def _download_asset_audio(media_url, asset):
        remote_filename = asset.audio.name
        local_filename = os.path.join(
            constants.MEDIA_DIR, remote_filename.replace('/', os.path.sep))

        if not os.path.exists(local_filename) or os.path.getsize(local_filename) != asset.audio_size:
            remote_url = media_url + remote_filename
            logger.info(f'sync: Downloading asset: {remote_url}')

            os.makedirs(os.path.dirname(local_filename), exist_ok=True)
            with requests.get(remote_url, stream=True) as response:
                response.raise_for_status()
                with open(local_filename, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
            return os.path.getsize(local_filename)
        else:
            return 0

    def load_asset_block(self):
        context = {
            'assets': [],
            'errors': [],
            'stopset': None,
            'wait': 60 * self.conf.wait_interval_minutes,
        }

        stopset = None
        stopsets = list(StopSet.objects.currently_enabled())

        # Randomly select stopsets and make sure they have rotators
        while stopsets:
            potential_stopset = random.choices(stopsets, weights=[float(s.weight) for s in stopsets], k=1)[0]
            stopsets.remove(potential_stopset)

            rotator_and_asset_list = potential_stopset.generate_asset_block()
            if any(asset for _, asset in rotator_and_asset_list):
                stopset = potential_stopset
                break

            else:
                context['errors'].append('No rotators or assets eligible to air found '
                                         f'in stop set {potential_stopset.name}.')

        if stopset:
            context['stopset'] = stopset.name

            for rotator, asset in rotator_and_asset_list:
                if asset:
                    context['assets'].append({
                        'rotator': rotator.name,
                        'color': rotator.color,
                        'name': asset.name,
                        'url': asset.audio.url,
                        'length': asset.duration.total_seconds(),
                    })
                else:
                    context['errors'].append(f"Stop set {stopset.name}'s rotator {rotator.name} "
                                             'has no assets eligible to air.')
        else:
            context['errors'].append('No stop sets with currently eligible to air.')

        if self.conf.wait_interval_subtracts_stopset_playtime:
            context['wait'] = round(max(0, context['wait'] - sum(a['length'] for a in context['assets'])))

        return context

    def _sync_log(self, time_period):
        # No sense wasting time doing DB aggregates if we're not in debug mode.
        if self.conf.debug:
            obj_counts = ', '.join(f'[{m._meta.verbose_name_plural} = {m.objects.count()}]' for m in (
                                   Asset, Rotator, StopSet, StopSetRotator, Asset.rotators.through))
            logger.info(f'sync: {time_period} sync, objects: {obj_counts}')

    def sync(self):
        self._execute_js_func('reportSyncProgress', 0)
        data = make_request('get', 'export')

        # 3% done after API response
        self._execute_js_func('reportSyncProgress', 3)
        self._sync_log('Starting')

        deserialized_objs = list(deserialize('python', data['objects']))
        bytes_synced = 0
        time_before = time.time()

        deserialized_assets = list(filter(lambda do: isinstance(do.object, Asset), deserialized_objs))

        for num_assets, deserialized_asset in enumerate(deserialized_assets, 1):
            bytes_synced += self._download_asset_audio(data['media_url'], deserialized_asset.object)
            # 99% done after assets sync'd
            self._execute_js_func('reportSyncProgress', 3 + (num_assets / len(deserialized_assets)) * 96)
        self._execute_js_func('reportSyncProgress', 99)

        if bytes_synced:
            logger.info(f'sync: Downloaded {bytes_synced} bytes of asset data in {time.time() - time_before:.3f}s.')

        pks = defaultdict(list)

        with transaction.atomic():
            for deserialized_obj in deserialized_objs:
                pks[deserialized_obj.object.__class__].append(deserialized_obj.object.pk)
                deserialized_obj.save()

            for model in (Asset, Rotator, StopSet, StopSetRotator):
                model.objects.exclude(pk__in=pks[model]).delete()

        # 100% after DB sync'd
        self._execute_js_func('reportSyncProgress', 100)

        self.conf.update(
            last_sync=datetime.datetime.now().strftime('%c'),
            **data['conf'],
        )

        self._sync_log('Completed')
    sync.use_own_thread = True


class TemplateAPI(APIBase):
    namespace = 'template'

    def render(self, template_name, context=None):
        return self.cef_window.render_template(template_name, context)


API_LIST = (AuthAPI, ConfigAPI, ModelsAPI, TemplateAPI)
