from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ...models import Lamning
from ...utilities import validate_geojson


class BBOXAPITest(TestCase):
    '''Tests of the bounding box API'''

    @classmethod
    def setUpTestData(cls):
        cls.headers = {
            'HTTP_USER_AGENT': 'Maskros',
        }

    def test_no_lamnings_valid_geojson(self):
        '''Test if the response is valid even if no lamnings are returned'''
        response = self.client.get(reverse('bbox') + '?south=59.061116905306505&east=16.42743057476074&north=59.105762247284275&west=16.321311213593557', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(validate_geojson(response.content), True)
        self.assertEqual(response['Content-Type'], 'application/geo+json')

    def test_missing_parameter(self):
        '''Test if the response is valid even if a parameter is missing'''
        response = self.client.get(reverse('bbox') + '?south=59.061116905306505&east=16.42743057476074&north=59.105762247284275', **self.headers)
        self.assertContains(response, 'Minst en parameter saknas.', status_code=400)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_parameter_wrong_format(self):
        '''Tests that invalid parameter values are rejected'''
        response = self.client.get(reverse('bbox') + '?south=blablabla&east=16.42743057476074&north=59.105762247284275&west=16.321311213593557', **self.headers)
        self.assertContains(response, 'Minst en parameter har ett felaktigt värde.', status_code=400)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_no_user_agent_error(self):
        '''Tests that the API returns an error if no user agent is set'''
        response = self.client.get(reverse('bbox') + '?south=59.061116905306505&east=16.42743057476074&north=59.105762247284275&west=16.321311213593557')
        self.assertContains(response, 'User-Agent saknas.', status_code=400)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_response_with_lamnings(self):
        '''Test if the response is valid and contains the correct lamnings'''
        user = User.objects.create_user(username='test', password='31(21)2HJHJ')
        user.save()

        lamning = Lamning.objects.create(
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            title='Test',
            description='Test beskrivning',
            user=user,
        )
        lamning.save()

        response = self.client.get(reverse('bbox') + '?south=60.06115&east=13.43&north=60.60&west=13.0557', **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(validate_geojson(response.content), True)
        self.assertEqual(response['Content-Type'], 'application/geo+json')
        self.assertContains(response, lamning.title)