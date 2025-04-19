import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AccountExportTest(TestCase):
    """Tests related to the Account export view"""

    def test_account_export(self):
        """Tests that the account export view returns the correct data"""
        user = User.objects.create_user(
            username="testuser",
            password="12345",
            is_superuser=True,
        )
        user.save()
        self.client.force_login(user=user)

        response = self.client.get(reverse("api_accounts_export"))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["@graph"]["@type"], "schema:Person")
        self.assertEqual(data["@graph"]["@id"], "#testuser")
        self.assertEqual(data["@graph"]["schema:alternateName"], "testuser")

    # TODO: add a test for users with a set display name

    def test_accoont_export_invalid(self):
        """Tests that the account export view returns 403 when the user is not logged in"""
        response = self.client.get(reverse("api_accounts_export"))
        self.assertEqual(response.status_code, 403)
