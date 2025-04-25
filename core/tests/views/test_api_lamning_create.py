import json

from django.contrib.auth.models import User
from django.http import HttpRequest
from django.test import TestCase, Client
from django.urls import reverse
from django.middleware.csrf import get_token

from ...models import AccessToken

class LamningCreateViewTestCase(TestCase):
    '''Tests for the view responsible for creating annotation links'''
    @classmethod
    def setUpTestData(cls):
        # Create a user
        cls.user = User.objects.create_user(
            username='testuser',
            password='12345',
        )
        cls.user.save()

        # create an access token for the user with read rights
        access_token = AccessToken.objects.create(
            user=cls.user,
            rights='w',
        )
        access_token.save()
        cls.user_access_token_write = access_token.token

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.url = reverse('api_lamning_create')

    def test_bad_access_token(self):
        # Test with an invalid access token
        response = self.client.post(
            self.url,
            data=json.dumps({'lamning': 'test'}), # we don't care about the content of the request
            content_type='application/geo+json',
            HTTP_AUTHORIZATION='Token invalid_token'
        )
        self.assertEqual(response.status_code, 403)

    def test_no_access_token_but_authenticated_user_no_csrf(self):
        # Test with no access token but authenticated user and no CSRF token
        self.client.login(username='testuser', password='12345')
        response = self.client.post(
            self.url,
            data=json.dumps({'lamning': 'test'}), # we don't care about the content of the request
            content_type='application/geo+json',
        )
        self.assertEqual(response.status_code, 403)

    def test_no_access_token_but_authenticated_user_with_bad_csrf(self):
        # Test with no access token but authenticated user and bad CSRF token
        self.client.login(username='testuser', password='12345')
        response = self.client.post(
            self.url,
            data=json.dumps({'lamning': 'test'}), # we don't care about the content of the request
            content_type='application/geo+json',
            HTTP_X_CSRFTOKEN='invalid_token'
        )
        self.assertEqual(response.status_code, 403)

    def test_no_access_token_but_authenticated_user_with_valid_csrf(self):
        # Test with no access token but authenticated user and valid CSRF token
        self.client.login(username='testuser', password='12345')

        # GET request to set the CSRF cookie
        self.client.get('/lamning/skapa-flera')

        csrf_token = self.client.cookies['csrftoken'].value

        response = self.client.post(
            self.url,
            data=json.dumps({'lamning': 'test'}), # we don't care about the content of the request
            content_type='application/geo+json',
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(response.status_code, 400)
