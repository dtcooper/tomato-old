import logging
from io import StringIO
import os

import django
from django.conf import settings
from django.core.management import call_command

from .cef import CefWindow
from .config import Config
from .constants import MEDIA_DIR, MEDIA_URL, USER_DIR

logger = logging.getLogger('tomato')


class Client:
    def __init__(self):
        os.makedirs(USER_DIR, exist_ok=True)

    def run(self):
        conf = Config()
        if conf.debug:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s [%(filename)s:%(lineno)s %(levelname)s] %(name)s: %(message)s')

        logger.info(f'Starting Tomato with configuration: {dict(conf)}')

        self.init_django()
        self.run_cef()

        logger.info(f'Tomato Exiting.')

    def init_django(self):
        settings.configure(
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': os.path.join(USER_DIR, 'db.sqlite3')}},
            DEBUG=False,
            INSTALLED_APPS=('tomato',),
            LOGGING_CONFIG=None,
            MEDIA_ROOT=MEDIA_DIR,
            MEDIA_URL=MEDIA_URL,
            USE_I18N=False,
            USE_TZ=True,
        )
        django.setup()

        migrate_output = StringIO()
        call_command('migrate', '--no-color', stdout=migrate_output)

        logger.info(f'Ran Django Migrations: {migrate_output.getvalue()}')

    def run_cef(self):
        cef_window = CefWindow()
        cef_window.run()
