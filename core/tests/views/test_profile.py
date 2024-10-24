from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ...models import User, UserDetails

class ProfileViewTest(TestCase):
    '''Tests for the profile view'''
    @classmethod
    def setUpTestData(cls):
        cls.members_only_user = User.objects.create_user(username='jskdk', password='31(21)2HJHJ')
        cls.members_only_user.save()
        members_only_user_details = UserDetails.objects.get(user=cls.members_only_user)
        members_only_user_details.profile_privacy = 'ME'
        members_only_user_details.save()

        cls.public_user = User.objects.create_user(username='ksdsgdgh', password='31(21)2HJHJ')
        cls.public_user.save()
        public_user_details = UserDetails.objects.get(user=cls.public_user)
        public_user_details.profile_privacy = 'PU'
        public_user_details.save()

        # private profile should be the default so no need to update UserDetails
        cls.private_user = User.objects.create_user(username='test', password='31(21)2HJHJ')
        cls.private_user.save()

        cls.inactive_user = User.objects.create_user(username='banned', password='hjhj', is_active=False)
        cls.inactive_user.save()

    def test_guest_cant_see_members_only_profile(self):
        response = self.client.get(reverse('profile', kwargs={'slug': self.members_only_user.username}))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    def test_member_can_see_members_only_profile(self):
        self.client.force_login(user=self.private_user)
        response = self.client.get(reverse('profile', kwargs={'slug': self.members_only_user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Vem som kan se din profil:')
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    def test_self_can_see_members_only_profile(self):
        self.client.force_login(user=self.members_only_user)
        response = self.client.get(reverse('profile', kwargs={'slug': self.members_only_user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vem som kan se din profil:')
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    def test_guest_cant_see_private_profile(self):
        response = self.client.get(reverse('profile', kwargs={'slug': self.private_user.username}))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    def test_member_cant_see_private_profile(self):
        self.client.force_login(user=self.members_only_user)
        response = self.client.get(reverse('profile', kwargs={'slug': self.private_user.username}))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
    
    def test_self_can_see_private_profile(self):
        self.client.force_login(user=self.private_user)
        response = self.client.get(reverse('profile', kwargs={'slug': self.private_user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vem som kan se din profil:')
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
    
    def test_guest_cant_see_inactive_profile(self):
        response = self.client.get(reverse('profile', kwargs={'slug': self.inactive_user.username}))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    def test_member_cant_see_inactive_profile(self):
        self.client.force_login(user=self.private_user)
        response = self.client.get(reverse('profile', kwargs={'slug': self.inactive_user.username}))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    def test_guest_can_see_public_profile(self):
        response = self.client.get(reverse('profile', kwargs={'slug': self.public_user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Vem som kan se din profil:')
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
        self.assertNotContains(response, 'Logga ut') # because of a previous bug causing visitors to appear logged in

    def test_member_can_see_public_profile(self):
        self.client.force_login(user=self.private_user)
        response = self.client.get(reverse('profile', kwargs={'slug': self.public_user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Vem som kan se din profil:')
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    def test_self_can_see_public_profile(self):
        self.client.force_login(user=self.public_user)
        response = self.client.get(reverse('profile', kwargs={'slug': self.public_user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vem som kan se din profil:')
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    def test_public_profile_renders_rss_link(self):
        response = self.client.get(reverse('profile', kwargs={'slug': self.public_user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '/ksdsgdgh/lamningar.rss')
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    def test_private_profile_does_not_render_rss_link(self):
        self.client.force_login(user=self.private_user)
        response = self.client.get(reverse('profile', kwargs={'slug': self.private_user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '/test/lamningar.rss')
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
