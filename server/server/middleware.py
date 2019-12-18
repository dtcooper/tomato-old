from django.contrib.auth.models import User
from django.contrib.auth.hashers import is_password_usable

from constance import config

from .models import ApiToken


class ServerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def set_user(self, request):
        token = request.headers.get('X-Auth-Token') or request.GET.get('auth_token')
        if token:
            request.user = ApiToken.user_from_token(token)

        if request.user.is_anonymous and config.ALLOW_ANONYMOUS_SUPERUSER:
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

    def set_timezone(self, request):
        pass

    def __call__(self, request):
        self.set_user(request)
        self.set_timezone(request)
        return self.get_response(request)
