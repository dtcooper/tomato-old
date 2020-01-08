import json

import requests

from .constants import REQUESTS_TIMEOUT


class AuthApi:
    def __init__(self, data, browser):
        self.data = data
        self.browser = browser

    def logout(self):
        self.data['client'].update({'auth_token': None, 'hostname': None})
        self.data.save()
        self.browser.ExecuteFunction('showLoginModal')

    def check_authorization(self):
        logged_in = False

        if self.data['client']['hostname'] and self.data['client']['auth_token']:
            logged_in = True  # In case of server error / no connectivity, assume login

            try:
                response = requests.get(f"{self.data['client']['hostname']}/ping", timeout=REQUESTS_TIMEOUT,
                                        headers={'X-Auth-Token': self.data['client']['auth_token']})
            except requests.RequestException:
                pass
            else:
                try:
                    logged_in = response.json()['valid_token']
                except (requests.JSONDecodeError, KeyError):
                    pass

        if logged_in:
            self.browser.ExecuteFunction('doLogin', None)
        else:
            self.browser.ExecuteFunction('showLoginModal')

    def login(self, username, password, protocol, hostname):
        error = None

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
                    self.data['client'].update({
                        'auth_token': auth_token,
                        'hostname': f'{protocol}://{hostname}',
                    })
                    self.data.save()

            elif response.status_code == 403:
                error = 'Invalid username or password.'
            else:
                error = 'Bad response from host.'

        self.browser.ExecuteFunction('doLogin', error)
