import json

import pytz

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.core.serializers import serialize
from django.http import HttpResponseForbidden, JsonResponse

from constance import config

from .models import ApiToken


def authenticate(request):
    response = HttpResponseForbidden()

    try:
        user = User.objects.get(username=request.POST.get('username', ''))
    except User.DoesNotExist:
        pass
    else:
        if user.check_password(request.POST.get('password', '')):
            response = JsonResponse({'token': ApiToken.generate(user)})

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

        objs = []
        for model_cls in apps.get_app_config('data').get_models():
            objs.extend(model_cls.objects.all())

        return JsonResponse({
            'config': options,
            'objects': json.loads(serialize('json', objs)),
        })
    return response
