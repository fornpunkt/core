from django.test import TestCase
from django.contrib.auth.models import User
from ...models import AccessToken

class AccessTokenTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.access_token = AccessToken.objects.create(user=self.user, rights='r')

    def test_access_token(self):
        '''Smoke test for the access token model'''
        self.assertEqual(len(self.access_token.token), 64)
