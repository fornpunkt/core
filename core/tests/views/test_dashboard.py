from unittest import skip
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ...models import Comment, Lamning


class DashboardViewTest(TestCase):
    '''Tests for the dashboard view'''
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='31(21)2HJHJ')
        cls.user.save()

    def test_no_lamningar(self):
        '''If no lamningar exist, an appropriate message is displayed.'''
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vi fann ej några lämningar.')
        self.assertQuerySetEqual(response.context['recent_lamnings'], [])

    def test_lamningar(self):
        '''If a lamning check that it's shown'''
        Lamning.objects.create(
            title='Testlämning',
            description='Testlämning',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            observation_type='FO',
            user=self.user,
        )
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Vi fann ej några lämningar.')
        self.assertContains(response, 'Testlämning')

    def is_redirected_to_landing_page(self):
        '''Tests that a logged out user is redirected to the landing page rather than the dashboard'''
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('landing'))

    def test_no_comments(self):
        '''If no comments exist, an appropriate message is displayed.'''
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vi fann ej några kommentarer.')
        self.assertQuerySetEqual(response.context['comments'], [])

    def test_comments(self):
        '''If another user has commented on your observation its comment is shown.'''
        lamning = Lamning.objects.create(
            title='Testlämning',
            description='Testlämning',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            observation_type='FO',
            user=self.user,
        )

        another_user  = User.objects.create_user(username='testuser2', password='31(21)2Hdsd=8JHJ')

        Comment.objects.create(
            user=another_user,
            content='En positiv kommentar',
            lamning=lamning,
        )

        self.client.force_login(user=self.user)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Vi fann ej några kommentarer.')
        self.assertContains(response, 'En positiv kommentar')

    @skip('TODO, not implemented')
    def test_comment_reply(self):
        '''Checks if a new comment to an observation by someone else but which you have commented earlier is shown'''
        another_user  = User.objects.create_user(username='testuser2', password='31(21)2Hdsd=8JHJ')

        lamning = Lamning.objects.create(
            title='Testlämning',
            description='Testlämning',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            observation_type='FO',
            user=another_user,
        )

        Comment.objects.create(
            user=self.user,
            content='En positiv kommentar',
            lamning=lamning,
        )

        Comment.objects.create(
            user=another_user,
            content='Åh, vad kul men en positiv kommentar',
            lamning=lamning,
        )

        self.client.force_login(user=self.user)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Vi fann ej några kommentarer.')
        self.assertContains(response, 'Åh, vad kul men en positiv kommentar')
