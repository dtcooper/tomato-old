import os
import platform
from urllib.parse import urljoin
from urllib.request import pathname2url

from cefpython3 import cefpython

from .version import __version__


class APIException(Exception):
    pass


IS_WINDOWS = platform.system() == 'Windows'
IS_MACOS = platform.system() == 'Darwin'

USER_DIR = os.path.join(os.path.expanduser('~'), '.tomato')
if IS_WINDOWS:
    try:
        USER_DIR = os.path.join(os.environ['LOCALAPPDATA'], 'Tomato')
    except KeyError:
        pass

MEDIA_DIR = os.path.join(USER_DIR, 'media')
MEDIA_URL = f'{urljoin("file:", pathname2url(MEDIA_DIR))}/'

WINDOW_SIZE_DEFAULT_WIDTH, WINDOW_SIZE_DEFAULT_HEIGHT = (900, 700)

API_ERROR_REQUESTS_TIMEOUT = 'Request timed out.'
API_ERROR_REQUESTS_ERROR = 'Bad response from host.'
API_ERROR_JSON_DECODE_ERROR = 'Invalid response format from host.'
API_ERROR_ACCESS_DENIED = 'Access denied.'
API_ERROR_INVALID_HTTP_STATUS_CODE = 'Bad response from host.'

REQUEST_TIMEOUT = 10
REQUEST_USER_AGENT = (f'tomato-client/{__version__} ({platform.system()} {platform.release()} '
                      f'{platform.machine()}) cefpython/{cefpython.__version__} ')
