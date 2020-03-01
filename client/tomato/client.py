import argparse
import logging
from io import StringIO
import os
import sys

import django
from django.conf import settings
from django.core.management import call_command

from .cef import CefWindow
from .config import Config
from .constants import MEDIA_DIR, MEDIA_URL, USER_DIR, IS_WINDOWS
from .version import __version__

if not IS_WINDOWS:
    import fcntl

logger = logging.getLogger('tomato')


class Client:
    def __init__(self):
        os.makedirs(USER_DIR, exist_ok=True)
        self.lockfile = None

    def ensure_not_running(self):
        # Adapted from
        # https://github.com/pycontribs/tendo/blob/master/tendo/singleton.py
        lockfile_path = os.path.join(USER_DIR, 'run.lock')
        is_running = False

        if IS_WINDOWS:
            try:
                if os.path.exists(lockfile_path):
                    os.remove(lockfile_path)

                self.lockfile = os.open(lockfile_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            except OSError as exception:
                if exception.errno == 13:
                    is_running = True

        else:
            self.lockfile = open(lockfile_path, 'w')
            self.lockfile.flush()

            try:
                fcntl.lockf(self.lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                is_running = True

        if is_running:
            logger.warn('Client already found running. Exiting')
            sys.exit(0)

    def parse_args(self):
        parser = argparse.ArgumentParser(description='Tomato Radio Automation', add_help=False,
                                         prog='tomato', epilog='...and remember kids, have fun!')
        parser.add_argument('-d', '--debug', action='store_true',
                            help="Run in debug mode. Use `-d' to debug just Tomato, and"
                                 "`--debug' to debug both CEF Python and Tomato.")
        parser.add_argument('--print-html', action='store_true', help='Print all rendered HTML templates.')
        parser.add_argument('--allow-multiple', action='store_true',
                            help='Allow multiple instances of Tomato to run at once.')
        parser.add_argument('-v', '--version', action='version', version=f'Tomato v{__version__}',
                            help="Show program's version number and exit.")
        parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                            help='Show this help message and exit.')
        return vars(parser.parse_args())

    def run(self):
        args = self.parse_args()
        conf = Config()
        conf._set_args(args)

        if conf.debug:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s [%(filename)s:%(lineno)s %(levelname)s] %(name)s: %(message)s')

        logger.info(f'Starting Tomato v{__version__} with configuration: {dict(conf)}')

        if not conf.allow_multiple:
            self.ensure_not_running()

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
