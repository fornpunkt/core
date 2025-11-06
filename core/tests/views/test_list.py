from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ...models import Lamning, List, ShadowLamning


class ListViewTest(TestCase):
    '''Tests for list views'''

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='test', password='31(21)2HJHJ')
        cls.user2 = User.objects.create_user(username='test2', password='31(21)2HJHJ')
        cls.user.save()
        cls.user2.save()

        cls.lamning = Lamning.objects.create(
            title='Testlämning',
            description='Testlämning',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            observation_type='FO',
            user=cls.user
        )
        cls.lamning.save()

        cls.list = List.objects.create(
            title='Test Lista',
            description='En testlista',
            user=cls.user,
            hidden=False
        )
        cls.list.lamnings.add(cls.lamning)
        cls.list.save()

        cls.hidden_list = List.objects.create(
            title='Dold Lista',
            description='En dold lista',
            user=cls.user,
            hidden=True
        )
        cls.hidden_list.save()

    def test_list_index_view(self):
        '''Test that the list index view works'''
        response = self.client.get(reverse('list_index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Lista')
        self.assertNotContains(response, 'Dold Lista')

    def test_list_detail_view(self):
        '''Test that the list detail view works'''
        response = self.client.get(reverse('list_detail', kwargs={'pk': self.list.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Lista')
        self.assertContains(response, 'En testlista')
        self.assertContains(response, 'Testlämning')

    def test_list_detail_hidden(self):
        '''Test that hidden lists are not accessible to other users'''
        response = self.client.get(reverse('list_detail', kwargs={'pk': self.hidden_list.pk}))
        self.assertEqual(response.status_code, 404)

    def test_list_detail_hidden_owner(self):
        '''Test that hidden lists are accessible to their owner'''
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('list_detail', kwargs={'pk': self.hidden_list.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dold Lista')

    def test_list_create_view_login_required(self):
        '''Test that creating a list requires login'''
        response = self.client.get(reverse('list_create'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_list_create_view(self):
        '''Test that creating a list works'''
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('list_create'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('list_create'), {
            'title': 'Ny Lista',
            'description': 'En ny lista',
            'hidden': False
        })
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertTrue(List.objects.filter(title='Ny Lista').exists())

    def test_list_update_view_owner_only(self):
        '''Test that only the owner can update a list'''
        self.client.force_login(user=self.user2)
        response = self.client.get(reverse('list_edit', kwargs={'pk': self.list.pk}))
        self.assertEqual(response.status_code, 404)

    def test_list_update_view(self):
        '''Test that updating a list works'''
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('list_edit', kwargs={'pk': self.list.pk}))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('list_edit', kwargs={'pk': self.list.pk}), {
            'title': 'Uppdaterad Lista',
            'description': 'Uppdaterad beskrivning',
            'hidden': False
        })
        self.assertEqual(response.status_code, 302)
        updated_list = List.objects.get(pk=self.list.pk)
        self.assertEqual(updated_list.title, 'Uppdaterad Lista')

    def test_list_delete_view_owner_only(self):
        '''Test that only the owner can delete a list'''
        self.client.force_login(user=self.user2)
        response = self.client.get(reverse('list_delete', kwargs={'pk': self.list.pk}))
        self.assertEqual(response.status_code, 404)

    def test_list_delete_view(self):
        '''Test that deleting a list works'''
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('list_delete', kwargs={'pk': self.list.pk}))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('list_delete', kwargs={'pk': self.list.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(List.objects.filter(pk=self.list.pk).exists())

    def test_user_lists_view(self):
        '''Test that user lists view shows only user's lists'''
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('user_lists'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Lista')
        self.assertContains(response, 'Dold Lista')

    def test_list_jsonld_view(self):
        '''Test that JSON-LD export works'''
        response = self.client.get(reverse('list_jsonld', kwargs={'pk': self.list.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/ld+json')

    def test_list_geojson_view(self):
        '''Test that GeoJSON export works'''
        response = self.client.get(reverse('list_geojson', kwargs={'pk': self.list.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/geo+json')

    def test_list_content_negotiation_jsonld(self):
        '''Test content negotiation for JSON-LD'''
        response = self.client.get(
            reverse('list_detail', kwargs={'pk': self.list.pk}),
            HTTP_ACCEPT='application/ld+json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/ld+json')

    def test_list_content_negotiation_geojson(self):
        '''Test content negotiation for GeoJSON'''
        response = self.client.get(
            reverse('list_detail', kwargs={'pk': self.list.pk}),
            HTTP_ACCEPT='application/geo+json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/geo+json')

    def test_list_export_api(self):
        '''Test that the list export API works'''
        self.client.force_login(user=self.user)

        # Test TSV export
        response = self.client.get(reverse('api_lists_export') + '?format=tsv')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/tsv')

        # Test GeoJSON export
        response = self.client.get(reverse('api_lists_export') + '?format=geojson')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/geo+json')

        # Test JSON-LD export (default)
        response = self.client.get(reverse('api_lists_export'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/ld+json')
