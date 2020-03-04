import itertools
import json
import os

from .client_server_constants import CLIENT_CONFIG_KEYS
from .constants import USER_DIR, WINDOW_SIZE_DEFAULT_HEIGHT, WINDOW_SIZE_DEFAULT_WIDTH


class Config:
    __instance = None
    __on_update = None
    DATA_FILE = os.path.join(USER_DIR, 'config.json')
    DEFAULTS = {
        'audio_device': None,
        'auth_token': None,
        'height': WINDOW_SIZE_DEFAULT_HEIGHT,
        'hostname': None,
        'last_sync': None,
        'protocol': 'https',
        'width': WINDOW_SIZE_DEFAULT_WIDTH,
    }
    DEFAULT_ARGS = {
        'allow_multiple': False,
        'debug': False,
        'print_html': False,
    }

    DEFAULTS.update(CLIENT_CONFIG_KEYS)

    def __new__(cls, *args, **kwargs):
        # Singleton
        if not cls.__instance:
            instance = super().__new__(cls)
            instance._init()
            cls.__instance = instance
        return cls.__instance

    def _init(self):
        self.__dict__.update({
            'args': self.DEFAULT_ARGS.copy(),
            'data': self.DEFAULTS.copy(),
        })

        if os.path.exists(self.DATA_FILE):
            with open(self.DATA_FILE) as file:
                self.data.update({k: v for k, v in json.load(file).items()
                                  if k not in self.DEFAULT_ARGS.keys()})
        else:
            self.save()

    def _set_args(self, args):
        self.args.update(args)

    def save(self):
        if self.__on_update:
            self.__on_update(dict(self))

        with open(self.DATA_FILE, 'w') as file:
            json.dump(self.data, file, indent=2, sort_keys=True)
            file.write('\n')

    def update(self, **kwargs):
        # If we have multiple keys to update, we can do that with only one save
        self.data.update(kwargs)
        self.save()

    @classmethod
    def register_on_update(cls, on_update):
        cls.__on_update = on_update

    def __getattr__(self, attr):
        try:
            return self.data[attr]
        except KeyError:
            try:
                # TODO: merge DEFAULT_ARGS into data, but then blacklist keys in save()
                return self.args[attr]
            except KeyError:
                raise AttributeError(f'Config entry not found: {attr}')

    def __setattr__(self, attr, value):
        self.data[attr] = value
        self.save()

    def __iter__(self):
        return itertools.chain(self.data.items(), self.args.items())
