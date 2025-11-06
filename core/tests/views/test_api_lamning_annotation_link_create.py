import json

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from ...models import AccessToken

class AnnotationLinkCreateViewTestCase(TestCase):
    '''Tests for the view responsible for creating annotation links'''
    fixtures = ['users.json', 'access_tokens.json', 'superuser.json']

    def setUp(self):
        self.superuser = User.objects.get(username='testsuperuser')
        self.user = User.objects.get(username='testuser')

        self.superuser_access_token_read = AccessToken.objects.get(user=self.superuser, rights='r').token
        self.superuser_access_token_write = AccessToken.objects.get(user=self.superuser, rights='w').token
        self.user_access_token_write = AccessToken.objects.get(user=self.user, rights='w').token

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
        content = json.loads(response.content)
        self.assertEqual(content['motivation'], 'linking')
        self.assertEqual(content['body']['schema:subjectOf']['@id'], self.sample_annotation_data['target'])
        self.assertEqual(content['target']['@id'], 'http://kulturarvsdata.se/raa/lamning/' + self.sample_annotation_data['subject'])

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
