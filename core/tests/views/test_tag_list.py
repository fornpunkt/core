from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ...models import CustomTag, Lamning

class TagListViewTest(TestCase):
    '''Tests for the tag list view'''

    def test_tags(self):
        '''If tags exist, they are displayed'''

        tag = CustomTag.objects.create(
            name='Testtagg',
            description='Testtagg',
        )
        tag.save()

        response = self.client.get(reverse('tag_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Testtagg')

    def test_no_tags(self):
        '''If no tags exist, an appropriate message is displayed.'''

        response = self.client.get(reverse('tag_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vi fann ej några taggar.')
        self.assertQuerySetEqual(response.context['page_obj'], [])

    def test_filter(self):
        '''Tests that the filter works'''

        # TODO split this into multiple tests
        tag = CustomTag.objects.create(
            name='Testtagg',
            description='Testtagg',
        )
        tag.save()

        response = self.client.get(reverse('tag_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Testtagg')
        self.assertContains(response, '<link rel="canonical" href="https://fornpunkt.se/taggar?sida=1">')

        response = self.client.get(reverse('tag_list') + '?filter=saknar_wikipedia')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Testtagg')
        self.assertContains(response, '<link rel="canonical" href="https://fornpunkt.se/taggar?sida=1&filter=saknar_wikipedia">')

        response = self.client.get(reverse('tag_list') + '?filter=saknar_wikipedia,saknar_beskrivning')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vi fann ej några taggar.')
        self.assertContains(response, '<link rel="canonical" href="https://fornpunkt.se/taggar?sida=1&filter=saknar_wikipedia,saknar_beskrivning">')

        response = self.client.get(reverse('tag_list') + '?filter=saknar_beskrivning')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vi fann ej några taggar.')
        self.assertContains(response, '<link rel="canonical" href="https://fornpunkt.se/taggar?sida=1&filter=saknar_beskrivning">')

        tag = CustomTag.objects.create(
            name='2esttagg2',
            wikipedia='https://sv.wikipedia.org/wiki/Testtagg',
        )
        tag.save()

        response = self.client.get(reverse('tag_list') + '?filter=saknar_wikipedia')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Testtagg')
        self.assertNotContains(response, '2esttagg2')
        self.assertContains(response, '<link rel="canonical" href="https://fornpunkt.se/taggar?sida=1&filter=saknar_wikipedia">')
