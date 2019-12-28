import pytz

from django.conf import settings
from django.contrib.auth.models import User
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
    return JsonResponse({'data': 'todo'})

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
