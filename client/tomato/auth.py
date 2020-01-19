from json.decoder import JSONDecodeError

import requests

from .config import Config
from .constants import REQUESTS_TIMEOUT


class AuthApi:
    namespace = 'auth'

    def __init__(self):
        self.conf = Config()

    def logout(self):
        self.conf.auth_token = None

    def check_authorization(self):
        logged_in = connected = False

        if all((self.conf.auth_token, self.conf.protocol, self.conf.hostname)):
            logged_in = True  # In case of server error / no connectivity, assume login

            try:
                response = requests.get(f'{self.conf.protocol}://{self.conf.hostname}/ping',
                                        timeout=REQUESTS_TIMEOUT, headers={'X-Auth-Token': self.conf.auth_token})
            except requests.RequestException:
                pass
            else:
                try:
                    logged_in = response.json()['valid_token']
                except (JSONDecodeError, KeyError):
                    pass
                else:
                    connected = True

        return (logged_in, connected)

    def login(self, username, password, protocol, hostname):
        error = None
        self.conf.update(hostname=hostname, protocol=protocol)

        try:
            response = requests.post(f'{protocol}://{hostname}/auth', timeout=REQUESTS_TIMEOUT,
                                     data={'username': username, 'password': password})
        except requests.RequestException:
            error = f'Timeout, bad hostname, or invalid protocol ({protocol}).'
        else:
            if response.status_code == 200:
                try:
                    auth_token = response.json()['auth_token']
                except (requests.JSONDecodeError, KeyError):
                    error = 'Bad response from host.'
                else:
                    self.conf.auth_token = auth_token

            elif response.status_code == 403:
                error = 'Invalid username or password.'
            else:
                error = 'Bad response from host.'

        return error
