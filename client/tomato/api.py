from collections import defaultdict
import datetime
import logging
from json.decoder import JSONDecodeError
import os

from django.core.serializers import deserialize
import requests

from . import constants
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

        # Guaranteed keys: error, status, valid
        data = {'error': None, 'status': -1}

        try:
            response = requests.request(method, f'{self.conf.protocol}://{self.conf.hostname}/{endpoint}',
                                        headers=headers, timeout=constants.REQUEST_TIMEOUT, **params)
        except Exception as e:
            if isinstance(e, requests.exceptions.Timeout):
                data['error'] = constants.API_ERROR_REQUESTS_TIMEOUT
                logger.exception(f'Request timed out (>{constants.REQUEST_TIMEOUT}s)')
            else:
                data['error'] = constants.API_ERROR_REQUESTS_ERROR
                logger.exception('Requests library threw an exception')

        else:
            data['status'] = response.status_code
            if response.status_code == 200:
                try:
                    data.update(response.json())
                except JSONDecodeError:
                    data['error'] = constants.API_ERROR_JSON_DECODE_ERROR
                    logger.exception('JSON decoding error')
            else:
                data['error'] = (constants.API_ERROR_ACCESS_DENIED if response.status_code == 403
                                 else constants.API_ERROR_INVALID_HTTP_STATUS_CODE)
                logger.error(f'API returned status code {response.status_code}')

        data['valid'] = not bool(data['error'])
        return data


make_request = make_request()


class AuthApi:
    namespace = 'auth'

    def __init__(self):
        self.conf = Config()

    def logout(self):
        self.conf.auth_token = None

    def check_authorization(self):
        logged_in = connected = False

        if self.conf.protocol and self.conf.hostname and self.conf.auth_token:
            response = make_request('get', 'ping')
            # If we got an HTTP status back, then we're "connected"
            connected = response['status'] != -1
            # If there's no valid token, default to whether we're connected or not
            # to allow for offline mode.
            logged_in = response.get('valid_token', not connected)

        return (logged_in, connected)

    def login(self, protocol, hostname, username, password):
        self.conf.update(hostname=hostname, protocol=protocol)
        response = make_request('post', 'auth', data={'username': username, 'password': password})
        self.conf.auth_token = response.get('auth_token')
        return response['error']


class ConfigApi:
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


class ModelsApi:
    namespace = 'models'

    def __init__(self):
        self.conf = Config()

    def sync(self):
        data = make_request('get', 'export')
        if not data['valid']:
            logger.error('Error synchronizing.')
            return

        self.conf.last_sync = datetime.datetime.now().strftime('%c')

        deserialized_objects = list(deserialize('python', data['objects']))

        for deserialized_object in deserialized_objects:
            if isinstance(deserialized_object.object, Asset):
                # TODO: download assets iff they don't already exist, wrap in try/except
                remote_filename = deserialized_object.object.audio.name
                local_filename = os.path.join(
                    constants.MEDIA_DIR, remote_filename.replace('/', os.path.sep))

                if not os.path.exists(local_filename):
                    logger.info(f'Downloading {remote_filename}')
                    os.makedirs(os.path.dirname(local_filename), exist_ok=True)

                    # TODO: Download to temp dir first
                    # NOTE the stream=True parameter below
                    with requests.get(data['media_url'] + remote_filename, stream=True) as response:
                        response.raise_for_status()
                        with open(local_filename, 'wb') as file:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    file.write(chunk)
                else:
                    logger.info(f'{remote_filename} already downloaded')

        existing_pks = defaultdict(list)

        # TODO: do in a transaction
        for obj in deserialize('python', data['objects']):
            existing_pks[obj.object.__class__].append(obj.object.pk)
            obj.save()

        for model in (Asset, Rotator, StopSet, StopSetRotator):
            model.objects.exclude(pk__in=existing_pks[model]).delete()
