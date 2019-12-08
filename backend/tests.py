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
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        expected_strings = (
            b'Tomato Radio Automation Administration'
            b'Audio Assets',
            b'Rotations',
            b'Stop Sets',
        )

        for expected_string in expected_strings:
            self.assertIn(expected_string, response.content)

    def test_app_index(self):
        pass
