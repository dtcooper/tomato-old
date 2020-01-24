from collections import defaultdict
import datetime
import logging
from json.decoder import JSONDecodeError
import os

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
        self.conf.update(hostname=hostname, protocol=protocol)
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
    def _download_asset_audio(media_url, asset):
        remote_filename = asset.audio.name
        local_filename = os.path.join(
            constants.MEDIA_DIR, remote_filename.replace('/', os.path.sep))

        if not os.path.exists(local_filename) or os.path.getsize(local_filename) != asset.audio_size:
            remote_url = media_url + remote_filename
            logger.info(f'Downloading asset: {remote_url}')

            os.makedirs(os.path.dirname(local_filename), exist_ok=True)
            with requests.get(remote_url, stream=True) as response:
                response.raise_for_status()
                with open(local_filename, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)

    def test_load_assets(self):
        return sorted(Asset.objects.values('name', 'audio'), key=lambda item: item['name'].lower())

    def sync(self):
        data = make_request('get', 'export')
        self.conf.last_sync = datetime.datetime.now().strftime('%c')

        deserialized_objs = list(deserialize('python', data['objects']))

        for deserialized_obj in deserialized_objs:
            if isinstance(deserialized_obj.object, Asset):
                self._download_asset_audio(data['media_url'], deserialized_obj.object)

        pks = defaultdict(list)

        with transaction.atomic():
            for deserialized_obj in deserialized_objs:
                pks[deserialized_obj.object.__class__].append(deserialized_obj.object.pk)
                deserialized_obj.save()

            for model in (Asset, Rotator, StopSet, StopSetRotator):
                pks_for_model = pks[model]
                logger.info(f'sync: Synchronized {len(pks_for_model)} {model._meta.verbose_name_plural}')
                model.objects.exclude(pk__in=pks_for_model).delete()

        # Optional TODO: delete unused asset files, perhaps on boot?
