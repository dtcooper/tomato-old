import datetime
import json
import os

from .constants import USER_DIR


def merge_into(src, dest):
    for k in src:
        if k in dest and isinstance(src[k], dict) and isinstance(dest[k], dict):
            merge_into(dest[k], src[k])
        else:
            dest[k] = src[k]


class Data:
    DATA_FILE = os.path.join(USER_DIR, 'data.json')
    DEFAULTS = {
        'auth_token': None,
        'debug': False,  # Needs to be set manually
        'hostname': None,
        'last_sync': None,
        'protocol': 'https',
    }

    def __init__(self):
        self.__dict__['data'] = self.DEFAULTS.copy()

        if os.path.exists(self.DATA_FILE):
            with open(self.DATA_FILE) as file:
                self.data.update(json.load(file))
        else:
            self.save()

    def save(self):
        with open(self.DATA_FILE, 'w') as file:
            json.dump(self.data, file, indent=2, sort_keys=True)
            file.write('\n')

    def update(self, **kwargs):
        # If we have multiple keys to update, we can do that with only one save
        self.data.update(kwargs)
        self.save()

    def __getattr__(self, attr):
        try:
            return self.data[attr]
        except KeyError:
            raise AttributeError(f'Data entry not found: {attr}')

    def __setattr__(self, attr, value):
        self.data[attr] = value
        self.save()


class DataApi:
    namespace = 'data'

    def __init__(self, data):
        self.data = data

    def get(self, attr):
        return getattr(self.data, attr)

    def get_many(self, *attrs):
        return [self.get(attr) for attr in attrs]

    def set(self, attr, value):
        setattr(self.data, attr, value)
