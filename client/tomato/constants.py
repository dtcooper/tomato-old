import os
import platform
import sys
from urllib.parse import urljoin
from urllib.request import pathname2url

from cefpython3 import cefpython

from .client_server_constants import (  # noqa
    ACTION_PLAYED_ASSET, ACTION_SKIPPED_ASSET, ACTION_PLAYED_STOPSET,
    ACTION_PLAYED_PARTIAL_STOPSET, ACTION_SKIPPED_STOPSET, ACTION_WAITED)
from .version import __version__


class APIException(Exception):
    def __init__(self, message, *extra_args):
        self.extra_args = extra_args
        super().__init__(message)


IS_WINDOWS = platform.system() == 'Windows'
IS_MACOS = platform.system() == 'Darwin'
IS_LINUX = platform.system() == 'Linux'
IS_FROZEN = getattr(sys, 'frozen', False)
VERSION = __version__

USER_DIR = os.path.join(os.path.expanduser('~'), '.tomato')
if IS_WINDOWS:
    try:
        USER_DIR = os.path.join(os.environ['LOCALAPPDATA'], 'Tomato')
    except KeyError:
        pass

# If it's a preview build, we namespace the USERDIR, so we can introduce breaking
# DB and config changes
if IS_FROZEN and 'preview' in VERSION:
    USER_DIR = f'{USER_DIR}-{VERSION}'

ASSETS_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'assets'))
TEMPLATES_DIR = os.path.join(ASSETS_DIR, 'templates')
APP_PATH = os.path.join(TEMPLATES_DIR, 'app.html')
APP_URL = urljoin('http://tomato', pathname2url(APP_PATH))

MEDIA_DIR = os.path.join(USER_DIR, 'media')
MEDIA_URL = f'{urljoin("http://tomato", pathname2url(MEDIA_DIR))}/'

WINDOW_SIZE_DEFAULT_WIDTH, WINDOW_SIZE_DEFAULT_HEIGHT = (925, 700)
WINDOW_SIZE_MIN_WIDTH, WINDOW_SIZE_MIN_HEIGHT = (800, 600)

API_ERROR_NO_HOSTNAME = 'Please provide a hostname.'
API_ERROR_NO_USERPASS = 'Please provide a username and password.'
API_ERROR_REQUESTS_TIMEOUT = 'Request timed out.'
API_ERROR_REQUESTS_ERROR = 'Bad response from host.'
API_ERROR_JSON_DECODE_ERROR = 'Invalid response format from host.'
API_ERROR_ACCESS_DENIED = 'Access denied.'
API_ERROR_INVALID_HTTP_STATUS_CODE = 'Bad response from host.'
API_ERROR_DB_MIGRATION_MISMATCH = 'Database version on server and client do not match.'

REQUEST_TIMEOUT = 10
REQUEST_USER_AGENT = (f'tomato-client/{__version__} ({platform.system()} {platform.release()} '
                      f'{platform.machine()}) cefpython/{cefpython.__version__} ')
