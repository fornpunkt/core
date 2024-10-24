from django.test import TestCase

from ...models import CustomTag, Lamning, User


class CustomTagModelTest(TestCase):
    """Tests the CustomTag model"""

    @classmethod
    def setUpTestData(cls):
        # tags are normaly created by being associated with a lamning so we do the same here

        cls.user = User.objects.create_user(username="test", password="31(21)2HJHJ")
        cls.user.save()

        cls.lamning = Lamning.objects.create(
            title="Testlämning",
            description="Testlämning",
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            observation_type="FO",
            user=cls.user,
        )

        # full tag sterilization must be tested through the form/create view it seems like
        cls.lamning.tags.add("Kolbotten", "Resmila")
        cls.lamning.save()

        cls.tag = CustomTag.objects.get(name="Resmila")

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
