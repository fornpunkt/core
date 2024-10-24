from django.test import TestCase
from django.contrib.auth.models import User

from ...models import UserDetails


class UserTestCase(TestCase):
    def test_user_details(self):
        '''Checks if user_details is populated when an user is created'''
        user = User.objects.create_user(username='testuser', password='31(21)2Hdsd=8JHJ')
        user.save()

        details = UserDetails.objects.get(user=user)
        self.assertEqual(details.profile_privacy, 'PR')
