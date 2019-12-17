from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import ApiToken


class DataAdminTests(TestCase):
    def setUp(self):
        self.super = User.objects.create_superuser(username='super', password='super')
        self.client = Client()

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
