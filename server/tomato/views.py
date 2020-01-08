import hashlib

import pytz

from django.conf import settings
from django.contrib.auth.models import User
from django.core import signing
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from constance import config

from version import __version__


def ping(request):
    return JsonResponse({
        'valid_token': request.valid_token,
        'software': f'tomato/{__version__}',
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


def export(request):
    response = HttpResponseForbidden()

    if request.user.is_authenticated or settings.DEBUG:
        options = {key.lower(): getattr(config, key) for key in dir(config)}
        options['wait_interval_minutes'] = max(0, options['wait_interval_minutes'])

        try:
            pytz.timezone(options['timezone'])
        except pytz.UnknownTimeZoneError:
            options['timezone'] = settings.TIME_ZONE

        return JsonResponse({
            'config': options,
            'objects': [],  # TODO
        })
    return response
