from collections import OrderedDict
import os

import pytz

from django.core import validators
from django.utils.html import format_html

BASE_DIR = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = 'hackme'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 3rd Paty
    'constance.backends.database',
    'constance',
    'django_extensions',

    # Local
    'tomato',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'tomato.middleware.ServerMiddleware',
]

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # Make sure tomato/admin/base_site.html overrides
            os.path.join(BASE_DIR, 'tomato', 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'constance.context_processors.config',
            ],
        },
    },
]

WSGI_APPLICATION = 'wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'HOST': 'db',
        'PORT': 5432,
    }
}

# Make sure  MemoryFileUploadHandler isn't set, because of data/models.py:Asset.clean()
FILE_UPLOAD_HANDLERS = ('django.core.files.uploadhandler.TemporaryFileUploadHandler',)

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'US/Pacific'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_URL = '/uploads/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'uploads')

SHELL_PLUS_PRINT_SQL = True
SHELL_PLUS_PRE_IMPORTS = [('constance', 'config')]

# TODO: 3. Store constants in common file, so it can be imported by client's config.py
CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_SUPERUSER_ONLY = False
CONSTANCE_ADDITIONAL_FIELDS = {
    'TIMEZONE': ('django.forms.fields.ChoiceField', {
        'widget': 'django.forms.Select',
        'choices': [(name, name) for name in pytz.common_timezones],
    }),
    'WAIT_INTERVAL_MINUTES': ('django.forms.fields.IntegerField', {
        'widget': 'django.forms.TextInput',
        'widget_kwargs': {'attrs': {'size': 10}},
        'validators': [validators.MinValueValidator(0), validators.MaxValueValidator(600)],
    }),
    'FADE_ASSETS_MS': ('django.forms.fields.IntegerField', {
        'widget': 'django.forms.TextInput',
        'widget_kwargs': {'attrs': {'size': 10}},
        'validators': [validators.MinValueValidator(0), validators.MaxValueValidator(10000)],
    }),
}
CONSTANCE_CONFIG = OrderedDict({
    'TIMEZONE': (TIME_ZONE, format_html(
        '{}<a href="{}" target="_blank">{}</a>{}',
        'Timezone for server/client to operate in. Choose from ',
        'https://en.wikipedia.org/wiki/List_of_tz_database_time_zones',
        'this list (TZ database name)', f'. (Defaults to {TIME_ZONE} if invalid.)'), 'TIMEZONE'),
    'WAIT_INTERVAL_MINUTES': (20, 'Time to wait between stop sets (in minutes).', 'WAIT_INTERVAL_MINUTES'),
    'WAIT_INTERVAL_SUBTRACTS_STOPSET_PLAYTIME': (
        False, 'Wait time subtracts the playtime of a stop set in minutes. This will provide more '
               'even results, ie the number of stop sets played per hour will be more consistent at'
               'the expense of a DJs air time.'),
    'FADE_ASSETS_MS': (
        0, 'Time at the beginning and end of each asset to fade in milliseconds '
           '(1000 milliseconds = 1 second). Leave this as at 0 to disable fading.', 'FADE_ASSETS_MS'),
    'STRIP_UPLOADED_AUDIO': (True, 'TODO'),
    # TODO: $ sox in.wav out.wav silence 1 0.1 1% reverse silence 1 0.1 1% reverse
})
CLIENT_CONFIG_KEYS = ('WAIT_INTERVAL_MINUTES', 'WAIT_INTERVAL_SUBTRACTS_STOPSET_PLAYTIME', 'FADE_ASSETS_MS')

# Valid file types as recognized by `soxi -t` and `file --mime-type` minus the audio/[x-]
VALID_AUDIO_FILE_TYPES = {
    '.mp3': {'soxi': 'mp3', 'mime': 'mpeg'},
    '.wav': {'soxi': 'wav', 'mime': 'wav'},
    '.ogg': {'soxi': 'vorbis', 'mime': 'ogg'},
    '.flac': {'soxi': 'flac', 'mime': 'flac'},
}

try:
    from local_settings import *  # noqa
except ImportError:
    pass
