from collections import namedtuple

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import Client, TestCase
from django.urls import reverse

from .models import Asset, RotatorAsset, Rotator, StopSet, StopSetRotator


Dataset = namedtuple('Dataset', ('asset', 'rotator', 'stopset'))


class DataAdminTests(TestCase):
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
            reverse('admin:app_list', args=('data',)),
            reverse('admin:data_asset_changelist'),
            reverse('admin:data_asset_add'),
            reverse('admin:data_asset_change', args=(data.asset.id,)),
            reverse('admin:data_rotator_changelist'),
            reverse('admin:data_rotator_add'),
            reverse('admin:data_rotator_change', args=(data.rotator.id,)),
            reverse('admin:data_stopset_changelist'),
            reverse('admin:data_stopset_add'),
            reverse('admin:data_stopset_change', args=(data.stopset.id,)),
        ):
            response = self.client.get(test_url)
            self.assertEqual(response.status_code, 200)

    def test_export_view(self):
        response = self.client.get(reverse('export'))
        self.assertEqual(response.status_code, 403)

        self.client.login(username='user', password='user')
        response = self.client.get(reverse('export'))
        self.assertEqual(response.status_code, 200)

        # TODO: test response value
