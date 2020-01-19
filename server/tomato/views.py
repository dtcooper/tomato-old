import hashlib
import itertools
from urllib.parse import urlparse

import pytz

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.core import signing
from django.core.serializers import serialize
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.gzip import gzip_page

from constance import config

from .version import __version__


def ping(request):
    return JsonResponse({
        'valid_token': request.valid_token,
        'software': f'tomato-server/{__version__}',
    })


@csrf_exempt
def authenticate(request):
    response = HttpResponseForbidden()

    try:
        user = User.objects.get(username=request.POST.get('username', ''))
    except User.DoesNotExist:
        pass
    else:
        if user.check_password(request.POST.get('password', '')):
            token = signing.dumps({
                'user_id': user.id,
                'pw_hash': hashlib.md5(user.password.encode('utf8')).hexdigest(),
            })
            response = JsonResponse({'auth_token': token})

    return response


@gzip_page
def export(request):
    response = HttpResponseForbidden()

    if request.user.is_authenticated:
        options = {key.lower(): getattr(config, key) for key in dir(config)}

        try:
            pytz.timezone(options['timezone'])
        except pytz.UnknownTimeZoneError:
            options['timezone'] = settings.TIME_ZONE

        media_url = urlparse(settings.MEDIA_URL)
        if not media_url.netloc:
            media_url = media_url._replace(netloc=request.get_host())
        if not media_url.scheme:
            media_url = media_url._replace(scheme=request.scheme)

        response = JsonResponse({
            'config': options,
            'media_url': media_url.geturl(),
            'objects': serialize('python', itertools.chain.from_iterable(
                cls.objects.all() for cls in apps.get_app_config('tomato').get_models())),
        })

    return response
