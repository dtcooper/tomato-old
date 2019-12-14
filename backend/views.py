from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden, JsonResponse

from .models import ApiToken, Asset, RotatorAsset, Rotator, StopSet, StopSetRotator


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

    if request.user.is_authenticated:
        response = JsonResponse({
            'timezone': settings.TIME_ZONE,
            'media_url': settings.MEDIA_URL,
            'objects': {
                model._meta.db_table: list(model.objects.order_by('id').values())
                for model in (Asset, RotatorAsset, Rotator, StopSet, StopSetRotator)
            },
        })

    return response
