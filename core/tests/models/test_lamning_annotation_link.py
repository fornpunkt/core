from django.test import TestCase
from django.urls import reverse

from ...models import Annotation


class KmrAnnotationLinkTest(TestCase):
    '''Tests relate to the LamningWikipediaLink model'''
    @classmethod
    def setUpTestData(cls):
        '''Tests that the wikipedia link is created correctly'''
        cls.annotation = Annotation.objects.create(
            subject='ca8d4036-5a16-4da6-80c9-8c0925b5b222',
            target='https://libris.kb.se/8ndlxxsw6zsbr9g6#it',
            title='Ett röse på ett röse? • ett nordgotländskt exempel på praktisk fjärranalys',
            publisher='Fornvännen',
            author_name_string='Gustafsson',
            target_type='Artikel',
        )
        cls.annotation.save()

    def test_annotation_link_uri(self):
        '''Tests that the wikipedia link uri is correct'''
        self.assertEqual(self.annotation.json_ld['@id'], f'https://fornpunkt.se/raa/lamning/ca8d4036-5a16-4da6-80c9-8c0925b5b222#annoteringar-{self.annotation.hashid}')

    def test_annotation_being_displayed(self):
        '''Tests that the annotation is displayed'''
        response = self.client.get(reverse('raa_lamning', kwargs={'record_id': 'ca8d4036-5a16-4da6-80c9-8c0925b5b222'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ett röse på ett röse? • ett nordgotländskt exempel på praktisk fjärranalys')
        self.assertContains(response, 'Fornvännen')
        self.assertContains(response, 'Gustafsson')
        self.assertContains(response, 'Artikel')
