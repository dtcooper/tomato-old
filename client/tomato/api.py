import logging
from json.decoder import JSONDecodeError

import requests

from .config import Config
from .constants import REQUEST_TIMEOUT, REQUEST_USER_AGENT


logger = logging.getLogger('tomato')

API_ERROR_REQUESTS_ERROR = 'Timeout or bad response from host.'
API_ERROR_JSON_DECODE_ERROR = 'Invalid response format from host.'
API_ERROR_ACCESS_DENIED = 'Access denied.'
API_ERROR_INVALID_HTTP_STATUS_CODE = 'Bad response from host.'


class make_request:
    def __init__(self):
        self.conf = Config()

    def __call__(self, method, endpoint, **params):
        headers = {'User-Agent': REQUEST_USER_AGENT}
        if self.conf.auth_token:
            headers['X-Auth-Token'] = self.conf.auth_token

        # Guaranteed keys: error, status, valid
        data = {'error': None, 'status': -1}

        try:
            response = requests.request(method, f'{self.conf.protocol}://{self.conf.hostname}/{endpoint}',
                                        headers=headers, timeout=REQUEST_TIMEOUT, **params)
        except Exception:
            data['error'] = API_ERROR_REQUESTS_ERROR
            logger.exception(API_ERROR_REQUESTS_ERROR)
        else:
            data['status'] = response.status_code
            if response.status_code == 200:
                try:
                    data.update(response.json())
                except JSONDecodeError:
                    data['error'] = API_ERROR_JSON_DECODE_ERROR
                    logger.exception(API_ERROR_JSON_DECODE_ERROR)
            else:
                data['error'] = (API_ERROR_ACCESS_DENIED if response.status_code == 403
                                 else API_ERROR_INVALID_HTTP_STATUS_CODE)
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
        return make_request('get', 'export')
