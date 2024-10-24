import geojson

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ...models import Lamning


class LamningGeoJsonViewTest(TestCase):
    '''Tests for the lamning geojson view'''
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='test', password='31(21)2HJHJ')
        cls.user.save()

        cls.lamning = Lamning.objects.create(
            title='Testlämning',
            description='Testlämning',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            observation_type='FO',
            user=cls.user
        )
        cls.lamning.tags.add('testtagg', 'testtagg_2')
        cls.lamning.save()

    def test_lamning_geojson(self):
        '''Smoke test for the lamning geojson view'''
        response = self.client.get(reverse('lamning_geojson', kwargs={'pk': self.lamning.pk}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response['Content-Type'], 'application/geo+json')
        self.assertEqual(response['Access-Control-Allow-Origin'], '*')

        parsed_geojson = geojson.loads(response.content)
        self.assertEqual(parsed_geojson['type'], 'Feature')
        self.assertEqual(parsed_geojson['geometry']['type'], 'Point')
        self.assertEqual(parsed_geojson['geometry']['coordinates'], [13.0743, 60.5963])
        self.assertEqual(parsed_geojson['properties']['title'], 'Testlämning')
        self.assertEqual(parsed_geojson['properties']['description'], 'Testlämning')
        self.assertEqual(parsed_geojson['properties']['observation_type'], 'falt')
