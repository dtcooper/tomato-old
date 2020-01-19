import os
import platform

from cefpython3 import cefpython

from .version import __version__


IS_WINDOWS = platform.system() == 'Windows'
IS_MACOS = platform.system() == 'Darwin'

USER_DIR = os.path.join(os.path.expanduser('~'), '.tomato')
if IS_WINDOWS:
    try:
        USER_DIR = os.path.join(os.environ['LOCALAPPDATA'], 'tomato')
    except KeyError:
        pass

WINDOW_SIZE_DEFAULT_WIDTH, WINDOW_SIZE_DEFAULT_HEIGHT = (900, 700)

REQUEST_TIMEOUT = 15
REQUEST_USER_AGENT = (f'tomato-client/{__version__} ({platform.system()} {platform.release()} '
                      f'{platform.machine()}) cefpython/{cefpython.__version__} ')
