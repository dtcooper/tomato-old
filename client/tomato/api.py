from collections import defaultdict
import datetime
import logging
from json.decoder import JSONDecodeError
import os
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


class AuthAPI:
    namespace = 'auth'

    def __init__(self):
        self.conf = Config()

    def logout(self):
        self.conf.auth_token = None

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

        return (logged_in, connected)

    def login(self, protocol, hostname, username, password):
        if not hostname:
            raise APIException(constants.API_ERROR_NO_HOSTNAME)

        self.conf.update(hostname=hostname, protocol=protocol)

        if not username or not password:
            raise APIException(constants.API_ERROR_NO_USERPASS)

        response = make_request('post', 'auth', data={'username': username, 'password': password})
        self.conf.auth_token = response.get('auth_token')


class ConfigAPI:
    namespace = 'conf'

    def __init__(self):
        self.conf = Config()

    def get(self, attr):
        return getattr(self.conf, attr)

    def get_many(self, *attrs):
        return [self.get(attr) for attr in attrs]

    def set(self, attr, value):
        setattr(self.conf, attr, value)

    def update(self, kwargs):
        self.conf.update(**kwargs)


class ModelsAPI:
    namespace = 'models'

    def __init__(self):
        self.conf = Config()

    @staticmethod
    def _clear_media_folder():
        db_asset_paths = {asset.audio.path for asset in Asset.objects.all()}

        for dirpath, dirnames, filenames in os.walk(constants.MEDIA_DIR):
            for filename in filenames:
                asset_path = os.path.join(dirpath, filename)
                if asset_path not in db_asset_paths:
                    logger.info(f'sync: Removing unused asset: {asset_path}')
                    os.remove(asset_path)

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
        context = {'wait': 60 * self.conf.wait_interval_minutes}
        stopset, rotator_and_asset_list = StopSet.generate_asset_block()

        if stopset:
            context.update({'stopset': stopset.name, 'assets': []})

            for rotator, asset in rotator_and_asset_list:
                asset_context = {'rotator': rotator.name, 'color': rotator.color}

                if asset:
                    asset_context.update({'name': asset.name, 'exists': True, 'url': asset.audio.url})
                else:
                    asset_context['exists'] = False

                context['assets'].append(asset_context)
        else:
            context['error'] = 'No stop sets with rotators currently eligible to air.'

        return context

    def _sync_log(self, time_period):
        # No sense wasting time doing DB aggregates if we're not in debug mode.
        if self.conf.debug:
            obj_counts = ', '.join(f'[{m._meta.verbose_name_plural} = {m.objects.count()}]' for m in (
                                   Asset, Rotator, StopSet, StopSetRotator, Asset.rotators.through))
            logger.info(f'sync: {time_period} sync, objects: {obj_counts}')

    def sync(self):
        data = make_request('get', 'export')
        self._sync_log('Starting')

        deserialized_objs = list(deserialize('python', data['objects']))
        bytes_synced = 0
        time_before = time.time()

        for deserialized_obj in deserialized_objs:
            if isinstance(deserialized_obj.object, Asset):
                bytes_synced += self._download_asset_audio(data['media_url'], deserialized_obj.object)

        if bytes_synced:
            logger.info(f'sync: Downloaded {bytes_synced} bytes of asset data in {time.time() - time_before:.3f}s.')

        pks = defaultdict(list)

        with transaction.atomic():
            for deserialized_obj in deserialized_objs:
                pks[deserialized_obj.object.__class__].append(deserialized_obj.object.pk)
                deserialized_obj.save()

            for model in (Asset, Rotator, StopSet, StopSetRotator):
                model.objects.exclude(pk__in=pks[model]).delete()

        self.conf.update(
            last_sync=datetime.datetime.now().strftime('%c'),
            **data['conf'],
        )

        self._clear_media_folder()
        self._sync_log('Completed')
