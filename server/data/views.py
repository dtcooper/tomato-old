from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse

from .models import Asset, Rotator, StopSet


def export(request):
    response = HttpResponseForbidden()

    if request.user.is_authenticated or settings.DEBUG:
        data = {'timezone': settings.TIME_ZONE}

        for model_cls in (Asset, Rotator, StopSet):
            data[model_cls._meta.db_table] = [
                obj.to_dict(request) for obj in model_cls.objects.all()]

        response = JsonResponse(data)

    return response
