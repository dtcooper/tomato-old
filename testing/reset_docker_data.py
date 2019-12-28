#!/usr/bin/env python

import datetime
import os
import random
import shutil
import subprocess
import sys

import django


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
    subprocess.call(['./manage.py', 'create_tomato_groups'])

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    django.setup()

    from django.contrib.auth.models import User

    from constance import config
    from tomato.models import Asset, Rotator, StopSet, StopSetRotator

    assets_upload_to = Asset._meta.get_field('audio').upload_to
    assets_upload_to_full_path = os.path.realpath(os.path.join(
        os.path.dirname(__file__), '..', 'server', 'uploads', assets_upload_to))
    subprocess.call(['mkdir', '-p', assets_upload_to_full_path])

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
        shutil.copy(filename, assets_upload_to_full_path)
        asset = Asset.objects.create(audio=f'{assets_upload_to}{filename}', **enabled_kwargs())
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
