from json.decoder import JSONDecodeError

import requests

from .constants import REQUESTS_TIMEOUT
from .data import Data


class AuthApi:
    namespace = 'auth'

    def __init__(self):
        self.data = Data()

    def logout(self):
        self.data.auth_token = None

    def check_authorization(self):
        logged_in = connected = False

        if all((self.data.auth_token, self.data.protocol, self.data.hostname)):
            logged_in = True  # In case of server error / no connectivity, assume login

            try:
                response = requests.get(f'{self.data.protocol}://{self.data.hostname}/ping',
                                        timeout=REQUESTS_TIMEOUT, headers={'X-Auth-Token': self.data.auth_token})
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
        self.data.update(hostname=hostname, protocol=protocol)

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
                    self.data.auth_token = auth_token

            elif response.status_code == 403:
                error = 'Invalid username or password.'
            else:
                error = 'Bad response from host.'

        return error
