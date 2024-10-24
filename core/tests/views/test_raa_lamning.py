from django.test import TestCase
from django.urls import reverse

from ...models import LamningWikipediaLink


class KmrWikipediaLinkTest(TestCase):
    '''Tests relate to LamningWikipediaLink annotations'''
    @classmethod
    def setUpTestData(cls):
        '''Tests that the wikipedia link is created correctly'''
        cls.wikipedia_link = LamningWikipediaLink.objects.create(
            kmr_lamning='401055fc-e795-4e2c-8e34-c45dfde18e61',
            wikipedia='https://sv.wikipedia.org/wiki/Nyk%C3%B6pingshus',
        )
        cls.wikipedia_link.save()

    def test_wikipedia_link_in_lamning_view(self):
        '''Tests that the wikipedia link is displayed in the lamning view'''
        response = self.client.get(reverse('raa_lamning', kwargs={'record_id': '401055fc-e795-4e2c-8e34-c45dfde18e61'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'https://sv.wikipedia.org/wiki/Nyk%C3%B6pingshus')
