from collections import namedtuple

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import Client, TestCase
from django.urls import reverse

from backend.models import ApiToken, Asset, RotatorAsset, Rotator, StopSet, StopSetRotator


Dataset = namedtuple('Dataset', ('asset', 'rotator', 'stopset'))


class BackendAdminTests(TestCase):
    def setUp(self):
        self.colors = {v: k for k, v in Rotator.COLOR_CHOICES}
        self.super = User.objects.create_superuser(username='super', password='super')
        self.user = User.objects.create_user(username='user', password='user')
        self.client = Client()

    def create_basic_data(self):
        rotator = Rotator.objects.create(name='rotator')
        asset = Asset()
        asset.audio.save('test.mp3', ContentFile('dummy data'))
        asset.save()
        RotatorAsset.objects.create(asset=asset, rotator=rotator)
        stopset = StopSet.objects.create(name='stopset')
        StopSetRotator.objects.create(stopset=stopset, rotator=rotator)

        return Dataset(asset, rotator, stopset)

    def test_admin_urls(self):
        self.client.login(username='super', password='super')
        data = self.create_basic_data()

        for test_url in (
            reverse('admin:index'),
            reverse('admin:app_list', args=('backend',)),
            reverse('admin:backend_asset_changelist'),
            reverse('admin:backend_asset_add'),
            reverse('admin:backend_asset_change', args=(data.asset.id,)),
            reverse('admin:backend_rotator_changelist'),
            reverse('admin:backend_rotator_add'),
            reverse('admin:backend_rotator_change', args=(data.rotator.id,)),
            reverse('admin:backend_stopset_changelist'),
            reverse('admin:backend_stopset_add'),
            reverse('admin:backend_stopset_change', args=(data.stopset.id,)),
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
        self.client.login(username='user', password='user')
        response = self.client.get(reverse('export'))
        self.assertEqual(response.status_code, 200)

        # TODO: test response value
