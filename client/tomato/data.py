from collections import UserDict
import copy
import json
import os

from .constants import USER_DIR


def merge_into(src, dest):
    for k in src:
        if k in dest and isinstance(src[k], dict) and isinstance(dest[k], dict):
            merge_into(dest[k], src[k])
        else:
            dest[k] = src[k]


class Data(UserDict):
    DATA_FILE = os.path.join(USER_DIR, 'data.json')
    DEFAULTS = {
        'last_sync': None,
        'client': {
            'auth_token': None,
            'hostname': None,
        },
        'objects': [],
    }

    def __init__(self):
        self.data = {}

        if os.path.exists(self.DATA_FILE):
            with open(self.DATA_FILE, 'r') as data_file:
                try:
                    self.data = json.load(data_file)
                except Exception:
                    pass

        merge_into(copy.deepcopy(self.DEFAULTS), self.data)

    def save(self):
        with open(self.DATA_FILE, 'w') as data_file:
            json.dump(self.data, data_file, sort_keys=True, indent=2)
            data_file.write('\n')
