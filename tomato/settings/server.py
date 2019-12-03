import os

from .base import *  # noqa


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql'
    }
}

try:
    # Settings local to site
    from .site import *  # noqa
except ImportError:
    pass
