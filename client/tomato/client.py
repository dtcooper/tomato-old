import os

import django
from django.conf import settings
from django.core.management import call_command

from .cef import run_cef_window
from .constants import MEDIA_DIR, USER_DIR


class Client:
    def __init__(self):
        os.makedirs(USER_DIR, exist_ok=True)

    def run(self):
        self.init_django()
        self.run_cef()

    def init_django(self):
        settings.configure(
            DEBUG=False,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': os.path.join(USER_DIR, 'db.sqlite3'),
                }
            },
            MEDIA_ROOT=MEDIA_DIR,
            INSTALLED_APPS=('tomato',),
            USE_TZ=True,
        )
        django.setup()
        call_command('migrate', verbosity=0)

    def run_cef(self):
        # Make sure Django is configured before importing so model import doesn't blow up
        from .api import AuthApi, ConfigApi, ModelsApi

        run_cef_window(AuthApi(), ConfigApi(), ModelsApi())
