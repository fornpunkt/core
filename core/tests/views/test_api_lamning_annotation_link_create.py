import json

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from ...models import AccessToken

class AnnotationLinkCreateViewTestCase(TestCase):
    '''Tests for the view responsible for creating annotation links'''
    @classmethod
    def setUpTestData(cls):
        # Create a superuser
        cls.superuser = User.objects.create_user(
            username='testsuperuser',
            password='12345',
            is_superuser=True,
        )
        cls.superuser.save()

        # Create a user
        cls.user = User.objects.create_user(
            username='testuser',
            password='12345',
        )
        cls.user.save()

        # create an access token for the superuser with read rights
        access_token = AccessToken.objects.create(
            user=cls.superuser,
            rights='r',
        )
        access_token.save()
        cls.superuser_access_token_read = access_token.token

        # create an access token for the superuser with write rights
        access_token = AccessToken.objects.create(
            user=cls.superuser,
            rights='w',
        )
        access_token.save()
        cls.superuser_access_token_write = access_token.token

        # create an access token for the user with write rights
        access_token = AccessToken.objects.create(
            user=cls.user,
            rights='w',
        )
        access_token.save()
        cls.user_access_token_write = access_token.token

    def setUp(self):
        self.client = Client()
        self.url = reverse('api_annotation_links_create')

        self.sample_annotation_data = {
            'subject': 'ca8d4036-5a16-4da6-80c9-8c0925b5b222',
            'title': 'Ett röse på ett röse? • ett nordgotländskt exempel på praktisk fjärranalys',
            'target_type': 'Artikel',
            'target': 'https://libris.kb.se/8ndlxxsw6zsbr9g6#it',
            'publisher': 'Fornvännen',
            'author_name_string': 'Anonymiserad',
        }

    def test_superuser_with_read_token(self):
        '''Tests that a superuser with a read token cannot create an annotation link'''

        response = self.client.post(self.url, data=self.sample_annotation_data, HTTP_AUTHORIZATION='Token ' + self.superuser_access_token_read)
        self.assertEqual(response.status_code, 403)

    def test_regular_user_with_write_token(self):
        '''Tests that a regular user with a write token cannot create an annotation link'''

        response = self.client.post(self.url, data=self.sample_annotation_data, HTTP_AUTHORIZATION='Token ' + self.user_access_token_write)
        self.assertEqual(response.status_code, 403)

    def test_request_without_token(self):
        '''Tests that a request without a token cannot create an annotation link'''

        response = self.client.post(self.url, data=self.sample_annotation_data)
        self.assertEqual(response.status_code, 403)

    def test_superuser_with_write_token(self):
        '''Tests that a superuser with a write token can create an annotation link'''

        response = self.client.post(self.url, data=self.sample_annotation_data, HTTP_AUTHORIZATION='Token ' + self.superuser_access_token_write)
        self.assertEqual(response.status_code, 201)
        json.loads(response.content)

    def test_superuser_with_write_token_and_missing_data(self):
        '''Tests that a superuser with a write token cannot create an annotation link if some requried data is missing'''

        data = self.sample_annotation_data
        del data['subject']
        response = self.client.post(self.url, data=data, HTTP_AUTHORIZATION='Token ' + self.superuser_access_token_write)
        self.assertEqual(response.status_code, 400)

    def test_superuser_with_write_token_and_invalid_target_type(self):
        '''Tests that a superuser with a write token cannot create an annotation link if the target type is invalid'''
        data = self.sample_annotation_data
        data['target_type'] = 'Invalid target type'
        response = self.client.post(self.url, data=data, HTTP_AUTHORIZATION='Token ' + self.superuser_access_token_write)
        self.assertEqual(response.status_code, 400)
