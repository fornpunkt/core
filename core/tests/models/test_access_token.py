from django.test import TestCase
from django.contrib.auth.models import User
from ...models import AccessToken

class AccessTokenTestCase(TestCase):
    fixtures = ['users.json', 'access_tokens.json']

    def test_access_token(self):
        '''Smoke test for the access token model'''
        access_token = AccessToken.objects.get(pk=1)
        self.assertEqual(len(access_token.token), 64)
