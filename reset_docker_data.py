#!/usr/bin/env python

import os
import subprocess

import django
from django.core.files import File


def main():
    os.chdir(os.path.dirname(__file__))

    subprocess.call(['rm', '-rf', 'uploads'])
    subprocess.call(['dropdb', '--if-exists', 'postgres'])
    subprocess.call(['createdb', 'postgres'])
    subprocess.call(['./manage.py', 'migrate'])

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tomato.settings')
    django.setup()

    from django.contrib.auth.models import User
    from backend.models import Asset, RotatorAsset, Rotator, StopSet, StopSetRotator

    User.objects.create_superuser(
        username='test',
        password='test',
        email='test@example.com',
        first_name='Test',
        last_name='User',
    )

    colors = {v: k for k, v in Rotator.COLOR_CHOICES}
    rotators = {
        'ad': Rotator.objects.create(name='ADs', color=colors['Light Blue']),
        'spotlight': Rotator.objects.create(name='Spotlight on Art', color=colors['Pink']),
        'station-id': Rotator.objects.create(name='Station IDs', color=colors['Orange']),
    }

    os.chdir('sample_sounds')
    for filename in os.listdir('.'):
        asset = Asset.objects.create(audio=File(open(filename, 'rb')))
        rotator = rotators[filename.rsplit('-', 1)[0]]
        RotatorAsset.objects.create(asset=asset, rotator=rotator)

    pre = StopSet.objects.create(name='Pre-event 1')
    StopSetRotator.objects.create(stopset=pre, rotator=rotators['station-id'])
    StopSetRotator.objects.create(stopset=pre, rotator=rotators['ad'])
    StopSetRotator.objects.create(stopset=pre, rotator=rotators['ad'])
    StopSetRotator.objects.create(stopset=pre, rotator=rotators['spotlight'])
    StopSetRotator.objects.create(stopset=pre, rotator=rotators['station-id'])
    during = StopSet.objects.create(name='During Event', enabled=False)
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
