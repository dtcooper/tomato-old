from collections import OrderedDict
import os

from django.utils.html import format_html

BASE_DIR = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = 'hackme'

DEBUG = True

ALLOWED_HOSTS = []

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
    'data',
    'server',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'server.middleware.ServerMiddleware',
]

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # Make sure server/admin/base_site.html overrides
            os.path.join(BASE_DIR, 'server', 'templates')
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

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_SUPERUSER_ONLY = False
CONSTANCE_CONFIG = OrderedDict({
    'TIMEZONE': (TIME_ZONE, format_html(
        '{}<a href="{}" target="_blank">{}</a>{}',
        'Timezone for server/client to operate in. Choose from ',
        'https://en.wikipedia.org/wiki/List_of_tz_database_time_zones',
        'this list (TZ database name)', f'. (Defaults to {TIME_ZONE} if invalid.)')),
    'WAIT_INTERVAL_MINUTES': (20, 'Time to wait between stop sets (in minutes).'),
    'WAIT_INTERVAL_SUBTRACTS_STOPSET_PLAYTIME': (
        False, 'Wait time subtracts the playtime of a stop set. This will provide more '
               'even results, ie the number of stop sets played per hour will be more '
               'consistent at the expense of a DJs air time.'),
    'NO_LOGIN_REQUIRED': (
        False, 'Allows anyone to access without authenticating. (WARNING: This '
               'is a potential security issue!)'),
    'STRIP_UPLOADED_AUDIO': (True, 'TODO'),
    'NORMALIZE_AUDIO_TO_MP3': (False, 'TODO'),
    'NORMALIZE_AUDIO_TO_MP3_BITRATE': (320, 'TODO'),
    # sox in.wav out.wav silence 1 0.1 1% reverse silence 1 0.1 1% reverse
})

# Valid file types as recognized by `soxi -t` => file extensions
VALID_FILE_TYPES_SOXI_TO_EXTENSIONS = {
    'mp3': 'mp3',
    'wav': 'wav',
    'vorbis': 'ogg',
    'flac': 'flac',
}


try:
    from local_settings import *  # noqa
except ImportError:
    pass
