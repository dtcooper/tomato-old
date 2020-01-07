import requests


class AuthApi:
    def __init__(self, data):
        self.data = data

    def login(self, username, password, proto, url, callback):
        response = requests.post(f'{proto}://{url}/auth', data={
            'username': username, 'password': password})
        print(response.json())
        callback.Call(True)
