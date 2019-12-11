from .base import *


def show_toolbar(request):
    if request.is_ajax():
        return False
    return True


if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
    DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': 'tomato.settings.runserver.show_toolbar'}

try:
    from .site import *
except ImportError:
    pass
