from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, JsonResponse

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
