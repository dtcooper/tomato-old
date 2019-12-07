#!/usr/bin/env python

import os
import shutil
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
    from backend.models import Asset, RotationAsset, Rotation, StopSet, StopSetRotation

    User.objects.create_superuser(
        username='test',
        password='test',
        email='test@example.com',
        first_name='Test',
        last_name='User',
    )

    colors = {color: hexcode for hexcode, color in Rotation._meta.get_field('color').choices}
    rotations = {
        'ad': Rotation.objects.create(name='ADs', color=colors['Light Blue']),
        'spotlight': Rotation.objects.create(name='Spotlight on Art', color=colors['Pink']),
        'station-id': Rotation.objects.create(name='Station IDs', color=colors['Orange']),
    }

    os.chdir('sample_sounds')
    for filename in os.listdir('.'):
        asset = Asset.objects.create(audio=File(open(filename, 'rb')))
        rotation = rotations[filename.rsplit('-', 1)[0]]
        RotationAsset.objects.create(asset=asset, rotation=rotation)

    pre = StopSet.objects.create(name='Pre-event 1')
    StopSetRotation.objects.create(stopset=pre, rotation=rotations['station-id'])
    StopSetRotation.objects.create(stopset=pre, rotation=rotations['ad'])
    StopSetRotation.objects.create(stopset=pre, rotation=rotations['ad'])
    StopSetRotation.objects.create(stopset=pre, rotation=rotations['spotlight'])
    StopSetRotation.objects.create(stopset=pre, rotation=rotations['station-id'])
    during = StopSet.objects.create(name='During Event', enabled=False)
    StopSetRotation.objects.create(stopset=during, rotation=rotations['station-id'])
    StopSetRotation.objects.create(stopset=during, rotation=rotations['spotlight'])
    StopSetRotation.objects.create(stopset=during, rotation=rotations['ad'])
    StopSetRotation.objects.create(stopset=during, rotation=rotations['spotlight'])
    StopSetRotation.objects.create(stopset=during, rotation=rotations['station-id'])


if __name__ == '__main__':
    if os.path.exists('/.dockerenv'):
        main()
    else:
        print('Must run in Docker container')
