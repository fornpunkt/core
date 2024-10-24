import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ...models import LamningWikipediaLink


class KmrWikipediaLinkExportTest(TestCase):
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

    def test_wikipedia_link_export(self):
        '''Tests that the wikipedia links are displayed in the wikipedia links export'''
        user = User.objects.create_user(
            username='testuser',
            password='12345',
            is_superuser=True,
        )
        user.save()
        self.client.force_login(user=user)

        response = self.client.get(reverse('api_wikipedia_links_export') + '?format=jsonld&scope=all')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'https://sv.wikipedia.org/wiki/Nyk%C3%B6pingshus')
        self.assertContains(response, 'https://sv.wikipedia.org/wiki/Kilakastalen')
        json.loads(response.content)
