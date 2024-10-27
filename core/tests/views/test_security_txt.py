import datetime

from django.test import TestCase

class SecurityTxtViewTest(TestCase):
    '''Tests for the security.txt view'''
    def test_security_txt(self):
        '''Tests that the security.txt view returns the correct content'''

        response = self.client.get('/.well-known/security.txt')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertContains(response, 'Contact: mailto:hej@fornpunkt.se')

        expires = response.content.decode('utf-8').splitlines()[2].replace('Expires: ', '')
        self.assertGreater(datetime.datetime.strptime(expires, '%Y-%m-%dT%H:%M:%S.%fZ'), datetime.datetime.now())
