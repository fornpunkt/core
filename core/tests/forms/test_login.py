from django.contrib.auth.models import User
from django.test import TestCase

from ...forms import LoginForm


class LoginFormTest(TestCase):
    '''Test for the login form'''
    fixtures = ['users.json']

    def test_login_with_uppercase_username(self):
        '''Test that login works with uppercase username'''

        data = {
            'username': 'tesTuser',
            'password': '31(21)2HJHJ'
        }
        form = LoginForm(None, data)
        self.assertTrue(form.is_valid())

    def test_login_with_wrong_username(self):
        '''Test that login fails with wrong username'''

        data = {
            'username': 'wrong_username',
            'password': '31(21)2HJHJ'
        }
        form = LoginForm(None, data)
        self.assertFalse(form.is_valid())
