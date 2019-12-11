from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import Client, TestCase

from backend.models import Asset, RotationAsset, Rotation, StopSet, StopSetRotation


class BackendAdminTests(TestCase):
    def setUp(self):
        self.colors = {v: k for k, v in Rotation.COLOR_CHOICES}
        User.objects.create_superuser(
            username='test',
            email='test@example.com',
            password='test'
        )
        self.client = Client()
        self.client.login(username='test', password='test')

    def test_basic_urls(self):
        rotation = Rotation.objects.create(name='rotation')
        asset = Asset()
        asset.audio.save('test.mp3', ContentFile('dummy data'))
        asset.save()
        RotationAsset.objects.create(asset=asset, rotation=rotation)
        stopset = StopSet.objects.create(name='stopset')
        StopSetRotation.objects.create(stopset=stopset, rotation=rotation)

        urls = (
            '/', '/backend/',
            '/backend/rotation/',
            '/backend/rotation/add/',
            f'/backend/rotation/{rotation.id}/change/',
            '/backend/asset/',
            '/backend/asset/add/',
            f'/backend/asset/{asset.id}/change/',
            '/backend/stopset/',
            '/backend/stopset/add/',
            f'/backend/stopset/{stopset.id}/change/',
        )

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200,
                             f'{url} status code {response.status_code} != 200')
