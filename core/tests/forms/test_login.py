from django.contrib.auth.models import User
from django.test import TestCase

from ...forms import LoginForm


class LoginFormTest(TestCase):
    '''Test for the login form'''

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='31(21)2HJHJ')
        cls.user.save()

    data = {
        'username': 'tesTuser',
        'password': '31(21)2HJHJ'
    }

    def test_login_with_uppercase_username(self):
        '''Test that login works with uppercase username'''

        form = LoginForm(None, self.data)
        self.assertTrue(form.is_valid())

    def test_login_with_wrong_username(self):
        '''Test that login fails with wrong username'''

        self.data['username'] = 'wrong_username'
        form = LoginForm(None, self.data)
        self.assertFalse(form.is_valid())
