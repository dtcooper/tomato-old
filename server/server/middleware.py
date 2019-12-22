import pytz

from django.contrib.auth.models import User
from django.utils import timezone

from constance import config

from .models import ApiToken


class ServerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def set_user(self, request):
        if config.NO_LOGIN_REQUIRED:
            user, _ = User.objects.update_or_create(
                username='anonymous_superuser',
                defaults={
                    'first_name': 'Anonymous',
                    'last_name': 'User',
                    'is_active': True,
                    'is_staff': True,
                    'is_superuser': True,
                }
            )

            if user.has_usable_password():
                user.set_unusable_password()
                user.save()

            request.user = user

        else:
            token = request.headers.get('X-Auth-Token') or request.GET.get('auth_token')
            if token:
                request.user = ApiToken.user_from_token(token)

    def set_timezone(self, request):
        try:
            tz = pytz.timezone(config.TIMEZONE)
        except pytz.UnknownTimeZoneError:
            pass
        else:
            timezone.activate(tz)

    def __call__(self, request):
        self.set_user(request)
        self.set_timezone(request)
        return self.get_response(request)
