from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import Client, TestCase

from backend.models import Asset, RotatorAsset, Rotator, StopSet, StopSetRotator


class BackendAdminTests(TestCase):
    def setUp(self):
        self.colors = {v: k for k, v in Rotator.COLOR_CHOICES}
        User.objects.create_superuser(
            username='test',
            email='test@example.com',
            password='test'
        )
        self.client = Client()
        self.client.login(username='test', password='test')

    def test_basic_urls(self):
        rotator = Rotator.objects.create(name='rotator')
        asset = Asset()
        asset.audio.save('test.mp3', ContentFile('dummy data'))
        asset.save()
        RotatorAsset.objects.create(asset=asset, rotator=rotator)
        stopset = StopSet.objects.create(name='stopset')
        StopSetRotator.objects.create(stopset=stopset, rotator=rotator)

        for test_url in (
            '/', '/backend/',
            '/backend/rotator/',
            '/backend/rotator/add/',
            f'/backend/rotator/{rotator.id}/change/',
            '/backend/asset/',
            '/backend/asset/add/',
            f'/backend/asset/{asset.id}/change/',
            '/backend/stopset/',
            '/backend/stopset/add/',
            f'/backend/stopset/{stopset.id}/change/',
        ):
            response = self.client.get(test_url)
            self.assertEqual(response.status_code, 200,
                             f'{test_url} status code {response.status_code} != 200')
