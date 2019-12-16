from .models import ApiToken


class AuthTokenAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = request.headers.get('X-Auth-Token') or request.GET.get('auth_token')
        if token:
            request.user = ApiToken.user_from_token(token)

        return self.get_response(request)
