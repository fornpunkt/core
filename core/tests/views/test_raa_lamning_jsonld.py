import json

from django.test import TestCase
from django.urls import reverse

from ...models import LamningWikipediaLink


class KmrWikipediaLinkTest(TestCase):
    '''Tests relate to the LamningWikipediaLink model'''
    @classmethod
    def setUpTestData(cls):
        '''Tests that the wikipedia link is created correctly'''
        cls.wikipedia_link = LamningWikipediaLink.objects.create(
            kmr_lamning='401055fc-e795-4e2c-8e34-c45dfde18e61',
            wikipedia='https://sv.wikipedia.org/wiki/Nyk%C3%B6pingshus',
        )
        cls.wikipedia_link.save()

        cls.wikipedia_link_2 = LamningWikipediaLink.objects.create(
            kmr_lamning='cb7f8403-4ec6-4081-966b-a04285105fb4',
            wikipedia='https://sv.wikipedia.org/wiki/Kilakastalen',
        )
        cls.wikipedia_link_2.save()

    def test_wikipedia_link_in_lamning_jsonld_view(self):
        '''Tests that the wikipedia link is displayed in the lamning jsonld view'''
        response = self.client.get(reverse('raa_lamning_jsonld', kwargs={'record_id': 'cb7f8403-4ec6-4081-966b-a04285105fb4'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'https://sv.wikipedia.org/wiki/Kilakastalen')
        self.assertNotContains(response, 'https://sv.wikipedia.org/wiki/Nyk%C3%B6pingshus')
        json.loads(response.content)
