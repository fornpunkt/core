from django.test import TestCase
from django.urls import reverse

from ...models import Lamning, User

class LamningModelTest(TestCase):
    '''Tests the Lamning model'''
    fixtures = ['users.json', 'lamnings.json']

    def setUp(self):
        # Add tags to the test lamning
        lamning = Lamning.objects.get(pk=1)
        lamning.tags.add('testtagg', 'testtagg_2')
        lamning.save()

    def test_lamning(self):
        '''Smoke test for the lamning model'''

        lamning = Lamning.objects.get(pk=1)
        self.assertEqual(lamning.tags.count(), 2)
        self.assertIn('inates":[13.0', lamning.geojson)

    def test_centeroid_generation(self):
        '''Test that centroid is generated correctly'''

        lamning = Lamning.objects.get(pk=1)
        self.assertEqual(lamning.center_lat, 60.5963)
        self.assertEqual(lamning.center_lon, 13.0743)
