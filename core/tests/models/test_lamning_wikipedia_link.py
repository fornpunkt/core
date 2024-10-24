from django.test import TestCase

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

    def test_wikipedia_link_uri(self):
        '''Tests that the wikipedia link uri is correct'''
        self.assertEqual(self.wikipedia_link.json_ld['@id'], f'https://fornpunkt.se/raa/lamning/401055fc-e795-4e2c-8e34-c45dfde18e61#annoteringar-w_{self.wikipedia_link.hashid}')
