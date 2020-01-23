import json
import os

from .constants import USER_DIR, WINDOW_SIZE_DEFAULT_WIDTH, WINDOW_SIZE_DEFAULT_HEIGHT


class Config:
    __instance = None
    DATA_FILE = os.path.join(USER_DIR, 'config.json')
    DEFAULTS = {
        'auth_token': None,
        'debug': bool(os.environ.get('TOMATO_DEBUG')),  # Manually override
        'height': WINDOW_SIZE_DEFAULT_HEIGHT,
        'hostname': None,
        'last_sync': None,
        'protocol': 'https',
        'width': WINDOW_SIZE_DEFAULT_WIDTH,
    }

    def __new__(cls, *args, **kwargs):
        # Singleton
        if not cls.__instance:
            instance = super().__new__(cls)
            instance.__dict__['data'] = cls.DEFAULTS.copy()

            if os.path.exists(cls.DATA_FILE):
                with open(cls.DATA_FILE) as file:
                    instance.data.update(json.load(file))
            else:
                instance.save()

            cls.__instance = instance
        return cls.__instance

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

    def __iter__(self):
        return iter(self.data.items())
