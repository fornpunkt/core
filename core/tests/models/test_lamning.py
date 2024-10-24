from django.test import TestCase
from django.urls import reverse

from ...models import Lamning, User

class LamningModelTest(TestCase):
    '''Tests the Lamning model'''
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

        # full tag sterilization must be tested through the form/create view it seems like
        cls.lamning.tags.add('testtagg', 'testtagg_2')
        cls.lamning.save()

    def test_lamning(self):
        '''Smoke test for the lamning model'''

        lamning = Lamning.objects.get(id=self.lamning.id)
        self.assertEqual(lamning.tags.count(), 2)
        self.assertIn('inates":[13.0', lamning.geojson)

    def test_centeroid_generation(self):
        '''Test that centroid is generated correctly'''

        lamning = Lamning.objects.get(id=self.lamning.id)
        self.assertEqual(lamning.center_lat, 60.5963)
        self.assertEqual(lamning.center_lon, 13.0743)
