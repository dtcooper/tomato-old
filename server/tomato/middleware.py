import hashlib

import pytz

from django.contrib.auth.models import User
from django.core import signing
from django.utils import timezone

from constance import config


class ServerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def set_user_from_token(self, request):
        request.valid_token = False

        token = request.headers.get('X-Auth-Token') or request.GET.get('auth_token')
        if token:
            try:
                payload = signing.loads(token)
            except signing.BadSignature:
                pass
            else:
                try:
                    user = User.objects.get(id=payload['user_id'])
                except User.DoesNotExist:
                    pass
                else:
                    pw_hash = hashlib.md5(user.password.encode('utf8')).hexdigest()
                    if payload['pw_hash'] == pw_hash:
                        request.valid_token = True
                        request.user = user

    def set_timezone(self, request):
        try:
            tz = pytz.timezone(config.TIMEZONE)
        except pytz.UnknownTimeZoneError:
            pass
        else:
            timezone.activate(tz)

    def __call__(self, request):
        self.set_user_from_token(request)
        self.set_timezone(request)
        return self.get_response(request)
