from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ...models import Lamning


class LamningListViewTest(TestCase):
    '''Tests for the lamning list view'''
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='31(21)2HJHJ')
        cls.user.save()

    def test_no_lamningar(self):
        '''If no lamningar exist, an appropriate message is displayed.'''
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('list_lamning'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vi fann ej några lämningar.')
        self.assertQuerySetEqual(response.context['page_obj'], [])

    def test_lamningar(self):
        '''If lamningar exist, they are displayed'''
        self.client.force_login(user=self.user)

        lamning = Lamning.objects.create(
            title='Testlämning',
            description='Testlämning',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            observation_type='FO',
            user=self.user
        )

        response = self.client.get(reverse('list_lamning'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Testlämning')
        self.assertContains(response, '<link rel="canonical" href="https://fornpunkt.se/lamningar?sida=1">')

    def test_filter(self):
        '''Tests that the filter works'''
        self.client.force_login(user=self.user)

        lamning = Lamning.objects.create(
            title='Testlämning',
            description='Testlämning',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            observation_type='FO',
            user=self.user
        )

        response = self.client.get(reverse('list_lamning') + '?filter=saknar_taggar')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Testlämning')
        self.assertContains(response, '<link rel="canonical" href="https://fornpunkt.se/lamningar?sida=1&filter=saknar_taggar">')

        response = self.client.get(reverse('list_lamning') + '?filter=saknar_observationstyp')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vi fann ej några lämningar.')
        self.assertContains(response, '<link rel="canonical" href="https://fornpunkt.se/lamningar?sida=1&filter=saknar_observationstyp">')

        response = self.client.get(reverse('list_lamning') + '?filter=saknar_observationstyp,saknar_taggar')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vi fann ej några lämningar.')
        self.assertContains(response, '<link rel="canonical" href="https://fornpunkt.se/lamningar?sida=1&filter=saknar_observationstyp,saknar_taggar">')