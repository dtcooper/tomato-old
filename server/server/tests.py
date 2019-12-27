from collections import namedtuple
from base64 import b64decode

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import Client, TestCase
from django.urls import reverse

from data.models import Asset, Rotator, StopSet, StopSetRotator
from .models import ApiToken


Dataset = namedtuple('Dataset', ('asset', 'rotator', 'stopset'))


class ServerTests(TestCase):
    def setUp(self):
        self.colors = {v: k for k, v in Rotator.COLOR_CHOICES}
        self.user = User.objects.create_user(username='user', password='user')
        self.super = User.objects.create_superuser(username='super', password='super')
        self.client = Client()

    def create_basic_data(self):
        rotator = Rotator.objects.create(name='rotator')
        asset = Asset()
        asset.audio.save(
            # Smallest possible wav file :)
            'test.wav', ContentFile(b64decode(b'UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=')))
        asset.save()
        asset.rotators.add(rotator)
        stopset = StopSet.objects.create(name='stopset')
        StopSetRotator.objects.create(stopset=stopset, rotator=rotator)

        return Dataset(asset, rotator, stopset)

    def test_admin_urls(self):
        self.client.login(username='super', password='super')
        data = self.create_basic_data()

        for test_url in (
            reverse('admin:index'),
            reverse('admin:app_list', args=('data',)),
            reverse('admin:data_asset_changelist'),
            reverse('admin:data_asset_add'),
            reverse('admin:data_asset_change', args=(data.asset.id,)),
            reverse('admin:data_asset_upload'),
            reverse('admin:data_rotator_changelist'),
            reverse('admin:data_rotator_add'),
            reverse('admin:data_rotator_change', args=(data.rotator.id,)),
            reverse('admin:data_stopset_changelist'),
            reverse('admin:data_stopset_add'),
            reverse('admin:data_stopset_change', args=(data.stopset.id,)),
        ):
            response = self.client.get(test_url)
            self.assertEqual(response.status_code, 200)

    def test_authenticate_view(self):
        response = self.client.get(reverse('admin:index'))
        self.assertNotEqual(response.status_code, 200)

        response = self.client.post(reverse('auth'), data={'username': 'no', 'password': 'no'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(ApiToken.objects.count(), 0)
        response = self.client.post(reverse('auth'), data={'username': 'super', 'password': 'no'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(ApiToken.objects.count(), 0)

        response = self.client.post(reverse('auth'), data={'username': 'super', 'password': 'super'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ApiToken.objects.count(), 1)
        token = response.json()['token']
        self.assertEqual(ApiToken.objects.get(user=self.super).token, token)

        response = self.client.get(reverse('admin:index'), data={'auth_token': token})
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('admin:index'), HTTP_X_AUTH_TOKEN=token)
        self.assertEqual(response.status_code, 200)

    def test_export_view(self):
        response = self.client.get(reverse('export'))
        self.assertEqual(response.status_code, 403)

        self.client.login(username='user', password='user')
        response = self.client.get(reverse('export'))
        self.assertEqual(response.status_code, 200)

        # TODO: test response value
