from django.contrib.auth.models import User
from django.test import Client, TestCase


class BackendAdminTests(TestCase):
    def setUp(self):
        User.objects.create_superuser(
            username='test',
            email='test@example.com',
            password='test'
        )
        self.client = Client()
        self.client.login(username='test', password='test')

    def test_index(self):
        response = self.client.get('')
        self.assertEqual(response.status_code, 200)
