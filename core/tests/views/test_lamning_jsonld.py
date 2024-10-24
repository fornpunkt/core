import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from ...models import Lamning


class LamningJsonLdViewTest(TestCase):
    """Tests for the JSON-LD view"""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="test", password="31(21)2HJHJ")
        cls.user.save()

        cls.lamning = Lamning.objects.create(
            title="Testlämning",
            description="Testlämning",
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            observation_type="FO",
            user=cls.user,
        )
        cls.lamning.tags.add("testtagg", "testtagg_2")
        cls.lamning.save()

    def test_lamning_jsonld(self):
        """Smoke test for the lamning json-ld view"""
        response = self.client.get(reverse("lamning_jsonld", kwargs={"pk": self.lamning.pk}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response["Content-Type"], "application/ld+json")
        self.assertEqual(response["Access-Control-Allow-Origin"], "*")

        parsed_json = json.loads(response.content)
        context = parsed_json["@context"]
        graph = parsed_json["@graph"][0]
        self.assertEqual(context[0], "https://www.w3.org/ns/anno.jsonld")
        self.assertEqual(context[1]["@language"], "sv")
        self.assertEqual(graph["@type"], "schema:CreativeWork")
        self.assertEqual(graph["schema:name"], "Testlämning")
        self.assertEqual(graph["schema:text"], "Testlämning")
        self.assertEqual(graph["schema:contentLocation"]["schema:geo"]["@type"], "schema:GeoCoordinates")
        self.assertEqual(graph["schema:contentLocation"]["schema:geo"]["schema:latitude"], 60.5963)
        self.assertEqual(graph["schema:contentLocation"]["schema:geo"]["schema:longitude"], 13.0743)
        self.assertEqual(graph["schema:event"]["@type"], "https://fornpunkt.se/observationstyper#falt")
