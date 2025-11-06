from django.test import TestCase

from ...models import CustomTag, Lamning, User


class CustomTagModelTest(TestCase):
    """Tests the CustomTag model"""
    fixtures = ['users.json', 'lamnings.json']

    def setUp(self):
        # tags are normaly created by being associated with a lamning so we do the same here

        self.user = User.objects.get(username="test")

        self.lamning = Lamning.objects.get(pk=1)

        # full tag sterilization must be tested through the form/create view it seems like
        self.lamning.tags.add("Kolbotten", "Resmila")
        self.lamning.save()

        self.tag = CustomTag.objects.get(name="Resmila")

    def test_tag(self):
        """Smoke test for the CustomTag model"""
        self.assertEqual(self.tag.slug, "resmila")
        self.assertEqual(self.tag.name, "Resmila")
        self.assertEqual(self.tag.json_ld["@id"], "https://fornpunkt.se/tagg/resmila")
        self.assertEqual(self.tag.json_ld["schema:url"]["@id"], "https://fornpunkt.se/tagg/resmila")
        self.assertNotIn("schema:subjectOf", self.tag.json_ld)
        self.assertNotIn("schema:description", self.tag.json_ld)

    def test_tag_optional_properties(self):
        """Tests the JSON-LD steralization for optional properties"""
        self.assertEqual(len(self.tag.json_ld), 4)

        self.tag.wikipedia = "https://sv.wikipedia.org/wiki/Kolbotten"
        self.tag.description = "Hej 123"

        self.tag.save()

        self.assertEqual(len(self.tag.json_ld), 6)
        self.assertEqual(self.tag.json_ld["schema:description"], "Hej 123")
        self.assertEqual(self.tag.json_ld["schema:subjectOf"]["@id"], "https://sv.wikipedia.org/wiki/Kolbotten")
