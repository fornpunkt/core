from django.test import TestCase
import json # Added for manipulating GeoJSON in tests
from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError


from ...models import Lamning, User

class LamningModelTest(TestCase):
    '''Tests the Lamning model'''
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='test', password='31(21)2HJHJ')
        cls.user.save()

        cls.lamning = Lamning.objects.create(
            title='Testlämning',
            description='Testlämning',
            geojson='{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]}}',
            observation_type='FO',
            user=cls.user
        )

        # full tag sterilization must be tested through the form/create view it seems like
        cls.lamning.tags.add('testtagg', 'testtagg_2')
        cls.lamning.save()

    def test_lamning(self):
        '''Smoke test for the lamning model'''

        lamning = Lamning.objects.get(id=self.lamning.id)
        self.assertEqual(lamning.tags.count(), 2)

        # Parse the GeoJSON string to a Python dict for robust checking
        saved_geojson_dict = json.loads(lamning.geojson)
        expected_coordinates = [13.0743, 60.5963]

        self.assertEqual(saved_geojson_dict['type'], 'Feature')
        self.assertIn('geometry', saved_geojson_dict)
        self.assertEqual(saved_geojson_dict['geometry']['type'], 'Point')
        self.assertEqual(saved_geojson_dict['geometry']['coordinates'], expected_coordinates)

    def test_centeroid_generation(self):
        '''Test that centroid is generated correctly'''

        lamning = Lamning.objects.get(id=self.lamning.id)
        self.assertEqual(lamning.center_lat, 60.5963)
        self.assertEqual(lamning.center_lon, 13.0743)

    def test_geojson_sanitization_extra_top_level_properties(self):
        """Test that extra top-level properties are removed from GeoJSON."""
        geojson_with_extra = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [15.0, 65.0]},
            "properties": {"name": "Sanitize Test"},
            "extra_top_prop": "should_be_removed",
            "another_extra": 123
        }
        lamning = Lamning.objects.create(
            title='Sanitization Test Top Level',
            description='Testing sanitization',
            geojson=json.dumps(geojson_with_extra),
            observation_type='RO',
            user=self.user
        )
        lamning.save() # Trigger the save method where sanitization happens

        retrieved_lamning = Lamning.objects.get(id=lamning.id)
        saved_geojson_dict = json.loads(retrieved_lamning.geojson)

        expected_geojson_dict = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [15.0, 65.0]},
            "properties": {"name": "Sanitize Test"}
            # "id" and "bbox" could also be here if they were in the original and allowed
        }

        # Check that only allowed keys are present
        self.assertEqual(set(saved_geojson_dict.keys()), set(expected_geojson_dict.keys()))
        self.assertEqual(saved_geojson_dict["type"], expected_geojson_dict["type"])
        self.assertEqual(saved_geojson_dict["geometry"], expected_geojson_dict["geometry"])
        self.assertEqual(saved_geojson_dict["properties"], expected_geojson_dict["properties"])
        self.assertNotIn("extra_top_prop", saved_geojson_dict)
        self.assertNotIn("another_extra", saved_geojson_dict)
        self.assertEqual(retrieved_lamning.center_lon, 15.0) # Ensure centroid is still correct
        self.assertEqual(retrieved_lamning.center_lat, 65.0)

    def test_geojson_sanitization_extra_nested_properties_in_geometry(self):
        """Test that extra properties in nested geometry are removed."""
        geojson_with_nested_extra = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [16.0, 66.0],
                "extra_geom_prop": "remove_this"
            },
            "properties": {"name": "Nested Sanitize Test"}
        }
        lamning = Lamning.objects.create(
            title='Sanitization Test Nested',
            description='Testing nested sanitization',
            geojson=json.dumps(geojson_with_nested_extra),
            observation_type='FO',
            user=self.user
        )
        lamning.save()

        retrieved_lamning = Lamning.objects.get(id=lamning.id)
        saved_geojson_dict = json.loads(retrieved_lamning.geojson)

        expected_geometry = {"type": "Point", "coordinates": [16.0, 66.0]}
        self.assertEqual(saved_geojson_dict["geometry"], expected_geometry)
        self.assertNotIn("extra_geom_prop", saved_geojson_dict["geometry"])
        self.assertEqual(saved_geojson_dict["properties"], {"name": "Nested Sanitize Test"}) # Properties should be untouched

    def test_geojson_valid_geojson_unchanged(self):
        """Test that valid GeoJSON (no extra props) remains unchanged."""
        valid_geojson_str = '{"type":"Feature","geometry":{"type":"Point","coordinates":[13.5,60.5]},"properties":{"name":"Valid"}}'
        valid_geojson_dict = json.loads(valid_geojson_str)

        lamning = Lamning.objects.create(
            title='Valid GeoJSON Test',
            description='Testing valid GeoJSON',
            geojson=valid_geojson_str,
            observation_type='FO',
            user=self.user
        )
        lamning.save()

        retrieved_lamning = Lamning.objects.get(id=lamning.id)
        # Compare dicts for a more robust comparison than strings (which might have whitespace diffs)
        self.assertEqual(json.loads(retrieved_lamning.geojson), valid_geojson_dict)
        self.assertEqual(retrieved_lamning.center_lon, 13.5)
        self.assertEqual(retrieved_lamning.center_lat, 60.5)

    def test_geojson_empty_string_fails_validation(self):
        """Test that an empty GeoJSON string fails model validation via full_clean()."""
        lamning_empty_str = Lamning(
            title='Empty String GeoJSON',
            description='Test for empty geojson string',
            geojson="",
            observation_type='FO',
            user=self.user
        )
        with self.assertRaises(ValidationError) as cm:
            lamning_empty_str.full_clean()

        # Check that the error is related to the geojson field
        self.assertIn('geojson', cm.exception.error_dict)

    def test_geojson_none_value_fails_validation(self):
        """Test that None for GeoJSON fails model validation via full_clean() as field is not nullable/blankable."""
        lamning_none_geojson = Lamning(
            title='None GeoJSON Validation',
            description='Test for None geojson value',
            geojson=None,
            observation_type='FO',
            user=self.user
        )
        with self.assertRaises(ValidationError) as cm:
            lamning_none_geojson.full_clean()
        # Django's Model.clean_fields() raises ValidationError if a non-nullable/non-blankable field is None/empty.
        self.assertIn('geojson', cm.exception.error_dict)

    def test_geojson_feature_properties_preserved(self):
        """Test that the 'properties' object within a Feature is fully preserved."""
        geojson_with_complex_props = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [18.0, 68.0]},
            "properties": {
                "name": "Complex Props Test",
                "value": 42,
                "nested_dict": {"a": 1, "b": "text"},
                "list_val": [1, 2, "three"]
            },
            "extra_prop": "remove me" # this should be removed
        }
        lamning = Lamning.objects.create(
            title='Complex Properties Test',
            description='Testing complex properties',
            geojson=json.dumps(geojson_with_complex_props),
            observation_type='MO',
            user=self.user
        )
        lamning.save()

        retrieved_lamning = Lamning.objects.get(id=lamning.id)
        saved_geojson_dict = json.loads(retrieved_lamning.geojson)

        # The 'extra_prop' should be gone
        self.assertNotIn("extra_prop", saved_geojson_dict)
        # The 'properties' field itself should be identical to the original
        self.assertEqual(saved_geojson_dict["properties"], geojson_with_complex_props["properties"])
        # Geometry should be standard
        self.assertEqual(saved_geojson_dict["geometry"], {"type": "Point", "coordinates": [18.0, 68.0]})
