from django.apps import apps
from django.conf import settings
from django.core.serializers import serialize
from django.http import HttpResponse, HttpResponseForbidden


def export(request):
    response = HttpResponseForbidden()

    if request.user.is_authenticated or settings.DEBUG:
        objs = []
        for model_cls in apps.get_app_config('data').get_models():
            objs.extend(model_cls.objects.all())

        response = HttpResponse(serialize('xml', objs), content_type='text/xml')
    return response
