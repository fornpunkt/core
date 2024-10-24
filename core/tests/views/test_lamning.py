from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ...models import Lamning


class LamningViewTest(TestCase):
    '''Tests for the lamning view'''
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='test', password='31(21)2HJHJ')
        cls.user.save()

    def test_lamning(self):
        '''Tests that the lamning view works'''
        self.client.force_login(user=self.user)

        lamning = Lamning.objects.create(
            title='Testlämning',
            description='Testlämning',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            observation_type='FO',
            user=self.user
        )
        lamning.tags.add('testtagg', 'testtagg_2')
        lamning.save()

        response = self.client.get(reverse('lamning', kwargs={'pk': lamning.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Testlämning')
        self.assertContains(response, 'Fältobservation')
        self.assertContains(response, 'testtagg')

    def test_lamning_jsonld_content_negotiation(self):
        '''Tests that the lamning view returns jsonld when the Content-Type is jsonld'''

        lamning = Lamning.objects.create(
            title='Testlämning',
            description='Testlämning',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            observation_type='FO',
            user=self.user
        )
        lamning.tags.add('testtagg', 'testtagg_2')
        lamning.save()

        response = self.client.get(reverse('lamning', kwargs={'pk': lamning.pk}), HTTP_ACCEPT='application/ld+json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/ld+json')

    def test_lamning_content_negotiation_prioritization(self):
        '''Tests that the lamning view returns the correct content type when multiple content types are requested'''

        lamning = Lamning.objects.create(
            title='Testlämning',
            description='Testlämning',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            observation_type='FO',
            user=self.user
        )
        lamning.tags.add('testtagg', 'testtagg_2')
        lamning.save()

        response = self.client.get(reverse('lamning', kwargs={'pk': lamning.pk}), HTTP_ACCEPT='application/geo+json, application/ld+json, text/html')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/geo+json')

    
    def test_lamning_content_negotiation_fallback(self):
        '''Tests that the lamning view returns the correct content type when none is requested'''

        lamning = Lamning.objects.create(
            title='Testlämning',
            description='Testlämning',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            observation_type='FO',
            user=self.user
        )
        lamning.tags.add('testtagg', 'testtagg_2')
        lamning.save()

        response = self.client.get(reverse('lamning', kwargs={'pk': lamning.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    def test_remote_observation_lamning_comment(self):
        '''Tests that the lamning view presents a custom comment promt for remote observations'''

        lamning = Lamning.objects.create(
            title='Testlämning',
            description='Testlämning',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            observation_type='RO',
            user=self.user
        )
        lamning.tags.add('testtagg', 'testtagg_2')
        lamning.save()

        response = self.client.get(reverse('lamning', kwargs={'pk': lamning.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Detta är en fjärrobservation, kan du bekräfta den i fält eller bidra med mer information?')

    def test_non_remote_observation_lamning_comment(self):
        '''Tests that the lamning view does not present a custom comment promt for non remote observations'''

        lamning = Lamning.objects.create(
            title='Testlämning',
            description='Testlämning',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            observation_type='FO',
            user=self.user
        )

        response = self.client.get(reverse('lamning', kwargs={'pk': lamning.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Detta är en fjärrobservation, kan du bekräfta den i fält eller bidra med mer information?')

        lamning2 = Lamning.objects.create(
            title='Testlämning',
            description='Testlämning',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            user = self.user
        )

        response = self.client.get(reverse('lamning', kwargs={'pk': lamning2.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Detta är en fjärrobservation, kan du bekräfta den i fält eller bidra med mer information?')
        self.assertContains(response, 'Har du mer information om denna kulturlämning?')
