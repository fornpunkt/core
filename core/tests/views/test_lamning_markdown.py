from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ...models import Lamning


class LamningMarkdownViewTest(TestCase):
    '''Tests for the lamning markdown view'''
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='test', password='31(21)2HJHJ')
        cls.user.save()

        cls.lamning = Lamning.objects.create(
            title='Testlämning',
            description='Testlämning',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            observation_type='FO',
            user=cls.user
        )
        cls.lamning.tags.add('testtagg', 'testtagg_2')
        cls.lamning.save()

    def test_lamning_markdown(self):
        '''Smoke test for the lamning markdown view'''
        response = self.client.get(reverse('lamning_markdown', kwargs={'pk': self.lamning.pk}))
        self.assertEqual(response.status_code, 200)

        self.assertIn('text/markdown', response['Content-Type'])
        self.assertEqual(response['Access-Control-Allow-Origin'], '*')

        self.assertIn('# Testlämning', response.content.decode())
        self.assertIn('fältobservation', response.content.decode())
        self.assertIn('URI/Länk', response.content.decode()) # once upon a time ä wasnt rendered correctly
