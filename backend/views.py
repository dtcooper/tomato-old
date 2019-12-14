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

    if request.user.is_authenticated or settings.DEBUG:
        assets = []
        for asset in Asset.objects.order_by('id').values():
            audio_url = '{}{}'.format(settings.MEDIA_URL, asset['audio'])
            if '//' not in settings.MEDIA_URL:
                audio_url = request.build_absolute_uri(audio_url)
            asset['audio'] = audio_url
            assets.append(asset)

        objects = {
            model._meta.db_table: list(model.objects.order_by('id').values())
            for model in (RotatorAsset, Rotator, StopSet, StopSetRotator)
        }
        objects[Asset._meta.db_table] = assets

        response = JsonResponse({
            'timezone': settings.TIME_ZONE,
            'objects': assets,
        })

    return response
