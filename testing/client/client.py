#!/usr/bin/env python3

import django
from django.db import transaction
from django.conf import settings
from django.core.management import call_command
from django.core.serializers import deserialize

import requests

settings.configure(
    DEBUG=False,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'test.sqlite3',
        }
    },
    INSTALLED_APPS=('data',),
    USE_TZ=True,
)
django.setup()


def main():
    from data.models import Asset, Rotator, StopSet

    call_command('migrate', verbosity=0)

    models = (Asset, Rotator, StopSet)
    data = requests.get('http://localhost:5000/export')
    objects = deserialize('xml', data.text)

    with transaction.atomic():
        for model_cls in models:
            model_cls.objects.all().delete()

        for obj in objects:
            obj.save()

    for model_cls in models:
        print(model_cls.__name__)
        for obj in model_cls.objects.all():
            print(f' - {obj}')


if __name__ == '__main__':
    main()
