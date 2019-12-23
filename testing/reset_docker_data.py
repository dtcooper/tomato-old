#!/usr/bin/env python

import datetime
import os
import random
import subprocess
import sys

import django
from django.core.files import File


def enabled_kwargs():
    from django.utils import timezone

    begin = end = None
    enabled = True

    if random.randint(0, 5) == 0:
        enabled = False
    else:
        now = timezone.now()

        if random.randint(0, 3) == 0:
            begin = now - datetime.timedelta(seconds=random.randint(0, 60 * 60 * 24))
        if random.randint(0, 3) == 0:
            end = now + datetime.timedelta(seconds=random.randint(1, 60 * 60 * 24))

    return {'enabled': enabled, 'begin': begin, 'end': end}


def main():
    app_path = os.path.realpath(os.path.join(
        os.path.dirname(__file__), '..', 'server'))
    sounds_path = os.path.realpath(os.path.join(
        os.path.dirname(__file__), 'sample_sounds'))

    os.chdir(app_path)
    sys.path.insert(0, app_path)

    subprocess.call(['rm', '-rf', 'uploads'])
    subprocess.call(['dropdb', '--if-exists', 'postgres'])
    subprocess.call(['createdb', 'postgres'])
    subprocess.call(['./manage.py', 'migrate'])

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    django.setup()

    from django.contrib.auth.models import User

    from constance import config
    from data.models import Asset, Rotator, StopSet, StopSetRotator

    User.objects.create_superuser(username='test', password='test')
    config.NO_LOGIN_REQUIRED = True

    colors = {v: k for k, v in Rotator.COLOR_CHOICES}
    rotators = {
        'ad': Rotator.objects.create(name='ADs', color=colors['Light Blue']),
        'spotlight': Rotator.objects.create(name='Spotlight on Art', color=colors['Pink']),
        'station-id': Rotator.objects.create(name='Station IDs', color=colors['Orange']),
    }

    os.chdir(sounds_path)
    for filename in os.listdir('.'):

        asset = Asset.objects.create(audio=File(open(filename, 'rb')), **enabled_kwargs())
        rotator = rotators[filename.rsplit('-', 1)[0]]
        asset.rotators.add(rotator)

    pre = StopSet.objects.create(name='Pre-event 1', **enabled_kwargs())
    StopSetRotator.objects.create(stopset=pre, rotator=rotators['station-id'])
    StopSetRotator.objects.create(stopset=pre, rotator=rotators['ad'])
    StopSetRotator.objects.create(stopset=pre, rotator=rotators['ad'])
    StopSetRotator.objects.create(stopset=pre, rotator=rotators['spotlight'])
    StopSetRotator.objects.create(stopset=pre, rotator=rotators['station-id'])
    during = StopSet.objects.create(name='During Event', **enabled_kwargs())
    StopSetRotator.objects.create(stopset=during, rotator=rotators['station-id'])
    StopSetRotator.objects.create(stopset=during, rotator=rotators['spotlight'])
    StopSetRotator.objects.create(stopset=during, rotator=rotators['ad'])
    StopSetRotator.objects.create(stopset=during, rotator=rotators['spotlight'])
    StopSetRotator.objects.create(stopset=during, rotator=rotators['station-id'])


if __name__ == '__main__':
    if os.path.exists('/.dockerenv'):
        main()
    else:
        print('Must run in Docker container')
