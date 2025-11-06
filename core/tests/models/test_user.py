from django.test import TestCase
from django.contrib.auth.models import User

from ...models import UserDetails


class UserTestCase(TestCase):
    fixtures = ['users.json']

    def test_user_details(self):
        '''Checks if user_details is populated when an user is created'''
        user = User.objects.get(username='testuser')

        details = UserDetails.objects.get(user=user)
        self.assertEqual(details.profile_privacy, 'PR')
