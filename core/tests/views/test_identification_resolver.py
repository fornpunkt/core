from django.test import TestCase
from django.urls import reverse

class IdentificationResolverViewTest(TestCase):
    '''Tests the identification resolver API view'''

    def test_redirection_of_valid_lnumber(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': 'L2018:1200'}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'https://fornpunkt.se/raa/lamning/13dfb99b-db36-4ac6-975c-1bc606dea81b')

    def test_redirection_of_invalid_lnumber(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': 'L1998:99999'}))
        self.assertEqual(response.status_code, 404)

    def test_redirection_of_valid_uuid(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': '13dfb99b-db36-4ac6-975c-1bc606dea81b'}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'https://fornpunkt.se/raa/lamning/13dfb99b-db36-4ac6-975c-1bc606dea81b')

    def test_redirection_of_invalid_uuid(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': '9ce3e04e-7959-4075-b4dc-8f0cd2207304'}))
        self.assertEqual(response.status_code, 404)

    def test_redirection_of_bad_value(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': 'badvalue'}))
        self.assertEqual(response.status_code, 404)

    def test_print_of_valid_lnumber(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': 'L2018:1200'}) + '?plaintext=true')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.endswith(b'/raa/lamning/13dfb99b-db36-4ac6-975c-1bc606dea81b'))
        self.assertFalse(response.content.startswith(b'/raa/lamning/13dfb99b-db36-4ac6-975c-1bc606dea81b'))
        self.assertEqual(response['Content-Type'], 'text/plain')

    def test_print_of_invalid_lnumber(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': 'L1998:99999'}) + '?plaintext=true')
        self.assertEqual(response.status_code, 404)

    def test_print_of_valid_uuid(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': '13dfb99b-db36-4ac6-975c-1bc606dea81b'}) + '?plaintext=true')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.endswith(b'/raa/lamning/13dfb99b-db36-4ac6-975c-1bc606dea81b'))
        self.assertFalse(response.content.startswith(b'/raa/lamning/13dfb99b-db36-4ac6-975c-1bc606dea81b'))
        self.assertEqual(response['Content-Type'], 'text/plain')

    def test_print_of_invalid_uuid(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': '9ce3e04e-7959-4075-b4dc-8f0cd2207304'}) + '?plaintext=true')
        self.assertEqual(response.status_code, 404)

    def test_print_of_bad_value(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': 'badvalue'}) + '?plaintext=true')
        self.assertEqual(response.status_code, 404)

    def test_external_redirection_of_valid_lnumber(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': 'L2018:1200'}) + '?target=kulturarvsdata')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'https://kulturarvsdata.se/raa/lamning/13dfb99b-db36-4ac6-975c-1bc606dea81b')

    def test_external_redirection_of_invalid_lnumber(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': 'L1998:99999'}) + '?target=kulturarvsdata')
        self.assertEqual(response.status_code, 404)

    def test_external_redirection_of_valid_uuid(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': '13dfb99b-db36-4ac6-975c-1bc606dea81b'}) + '?target=kulturarvsdata')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, 'https://kulturarvsdata.se/raa/lamning/13dfb99b-db36-4ac6-975c-1bc606dea81b')

    def test_external_redirection_of_invalid_uuid(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': '9ce3e04e-7959-4075-b4dc-8f0cd2207304'}) + '?target=kulturarvsdata')
        self.assertEqual(response.status_code, 404)

    def test_external_redirection_of_bad_value(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': 'badvalue'}) + '?target=kulturarvsdata')
        self.assertEqual(response.status_code, 404)

    def test_external_print_of_valid_lnumber(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': 'L2018:1200'}) + '?plaintext=true&target=kulturarvsdata')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'https://kulturarvsdata.se/raa/lamning/13dfb99b-db36-4ac6-975c-1bc606dea81b')

    def test_external_print_of_invalid_lnumber(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': 'L1998:99999'}) + 'plaintext=true&target=kulturarvsdata')
        self.assertEqual(response.status_code, 404)

    def test_external_print_of_valid_uuid(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': '13dfb99b-db36-4ac6-975c-1bc606dea81b'}) + '?plaintext=true&target=kulturarvsdata')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'https://kulturarvsdata.se/raa/lamning/13dfb99b-db36-4ac6-975c-1bc606dea81b')

    def test_external_print_of_invalid_uuid(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': '9ce3e04e-7959-4075-b4dc-8f0cd2207304'}) + '?plaintext=true&target=kulturarvsdata')
        self.assertEqual(response.status_code, 404)

    def test_external_print_of_bad_value(self):
        response = self.client.get(reverse('identification_resolver', kwargs={'identifier': 'badvalue'}) + '?plaintext=true&target=kulturarvsdata')
        self.assertEqual(response.status_code, 404)
