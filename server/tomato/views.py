import hashlib
import itertools
from urllib.parse import urlparse


from django.conf import settings
from django.core import signing
from django.core.serializers import deserialize, serialize
from django.contrib.auth import authenticate, login
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.gzip import gzip_page
from django.urls import reverse

from constance import config

from .client_server_constants import CLIENT_CONFIG_KEYS
from .models import get_latest_tomato_migration, Asset, LogEntry, Rotator, StopSet, StopSetRotator
from .version import __version__


def ping(request):
    return JsonResponse({
        'latest_migration': get_latest_tomato_migration(),
        'valid_token': request.valid_token,
        'version': __version__,
    })


@csrf_exempt
def log(request):
    if request.user.is_authenticated and request.method == 'POST':
        for log_entry in deserialize('json', request.body):
            # Make sure we're only serializing log entries
            if isinstance(log_entry.object, LogEntry):
                log_entry.object.user_id = request.user.id
                log_entry.save()

        return HttpResponse()
    else:
        return HttpResponseForbidden()


@csrf_exempt
def auth(request):
    response = HttpResponseForbidden()
    user = authenticate(username=request.POST.get('username'),
                        password=request.POST.get('password'))
    if user:
        response = JsonResponse({'auth_token': signing.dumps({
            'user_id': user.id,
            'pw_hash': hashlib.md5(user.password.encode('utf8')).hexdigest(),
        })})

    return response


def token_login(request):
    response = HttpResponseForbidden()
    if request.valid_token:
        login(request, request.user)
        response = HttpResponseRedirect(reverse('admin:index'))
    return response


@gzip_page
def export(request):
    response = HttpResponseForbidden()

    if request.user.is_authenticated:
        # Make media_url absolute URL
        media_url = urlparse(settings.MEDIA_URL)
        if not media_url.netloc:
            media_url = media_url._replace(netloc=request.get_host())
        if not media_url.scheme:
            media_url = media_url._replace(scheme=request.scheme)

        response = JsonResponse({
            'conf': {key: getattr(config, key.upper()) for key in CLIENT_CONFIG_KEYS},
            'media_url': media_url.geturl(),
            'objects': serialize('python', itertools.chain.from_iterable(
                cls.objects.all() for cls in (Asset, Rotator, StopSet, StopSetRotator))),
        })

    return response
