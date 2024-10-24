from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.text import format_lazy


class SignUpForm(UserCreationForm):
    '''Custom signup form ensuring lowercase usernames'''
    email = forms.EmailField()
    user_terms_url = reverse_lazy('user_terms')
    privacy_policy_url = reverse_lazy('privacy_policy')

    accepted_terms = forms.BooleanField(
        required=True,
        label='Användarvillkor',
        help_text=mark_safe(format_lazy('Jag samtycker till <a href="{terms}">användarvillkoren<a/> och <a href="{privacy}">integritetspolicyn<a/>.', terms=user_terms_url, privacy=privacy_policy_url)),
        error_messages={
            'required': 'Du måste godkänna användarvillkoren för att kunna registrera dig.',
        }
    )

    class Meta:
        '''We add accepted_terms to the UserCreationForm and change the error message for username'''
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'accepted_terms')

        help_texts = {
            'username': mark_safe('Obligatoriskt. 150 tecken eller färre. Endast små bokstäver, siffror och <code>-</code>.'),
        }

    def clean_username(self):
        '''make all usernames lowercase'''
        username = self.cleaned_data.get('username')
        lowercase_username = username.lower()

        forbidden = ['@', '+', '_', '.']
        if any(char in forbidden for char in lowercase_username):
             raise forms.ValidationError('Användarnamnet får inte innehålla @, +, _, eller .')

        return lowercase_username

    def clean_email(self):
        '''we check that the email is unique, however, we do not enforce this in the db so that admins can still create users needing multiple accounts'''
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('En användare med den här e-postadressen finns redan.')
        return email


class LoginForm(AuthenticationForm):
    '''Custom login form ensuring lowercase usernames'''
    def clean(self):
        username = self.cleaned_data.get('username').lower()
        password = self.cleaned_data.get('password')

        if username is not None and password:
            self.user_cache = authenticate(
                self.request, username=username, password=password
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
