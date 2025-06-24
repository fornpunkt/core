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

    # The following three tests are older versions and will be replaced by the
    # "Existing tests adapted for new sanitization rules" section below.
    # def test_geojson_sanitization_extra_top_level_properties(self): ...
    # def test_geojson_sanitization_extra_nested_properties_in_geometry(self): ...
    # def test_geojson_valid_geojson_unchanged(self): ...

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

    # test_geojson_feature_properties_preserved is no longer relevant as properties are emptied.

    # --- Existing tests adapted for new sanitization rules ---

    def test_geojson_sanitization_extra_top_level_properties(self): # Was an old test, adapted
        """Test that extra top-level properties are removed and properties emptied."""
        geojson_with_extra = {
            "type": "Feature",
            "id": "f1", # should be removed
            "bbox": [-1,-1,1,1], # should be removed
            "geometry": {"type": "Point", "coordinates": [15.0, 65.0]},
            "properties": {"name": "Sanitize Test", "value": 1}, # should be emptied
            "extra_top_prop": "should_be_removed",
        }
        lamning = Lamning.objects.create(
            title='Sanitization Test Top Level',
            description='Testing sanitization',
            geojson=json.dumps(geojson_with_extra),
            observation_type='RO',
            user=self.user
        )
        lamning.save()

        retrieved_lamning = Lamning.objects.get(id=lamning.id)
        saved_geojson_dict = json.loads(retrieved_lamning.geojson)

        expected_geojson_dict = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [15.0, 65.0]},
            "properties": {} # Properties are emptied
        }

        self.assertEqual(saved_geojson_dict, expected_geojson_dict)
        self.assertEqual(retrieved_lamning.center_lon, 15.0)
        self.assertEqual(retrieved_lamning.center_lat, 65.0)

    def test_geojson_sanitization_extra_nested_properties_in_geometry(self): # Was an old test, adapted
        """Test that extra properties in nested geometry are removed and properties emptied."""
        geojson_with_nested_extra = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [16.0, 66.0],
                "extra_geom_prop": "remove_this", # Should be removed from geometry
                "bbox": [0,0,1,1] # Should be removed from geometry
            },
            "properties": {"name": "Nested Sanitize Test"} # Should be emptied
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
        self.assertEqual(saved_geojson_dict["properties"], {}) # Properties are emptied

    def test_geojson_valid_geojson_unchanged_except_properties_and_allowed_keys(self): # Was test_geojson_valid_geojson_unchanged
        """Test that valid GeoJSON has properties emptied and only allowed keys remain."""
        valid_geojson_dict_original = {
            "type":"Feature",
            "id": "featValid", # Will be removed
            "geometry":{"type":"Point","coordinates":[13.5,60.5]},
            "properties":{"name":"Valid", "value":10} # Will be emptied
        }

        lamning = Lamning.objects.create(
            title='Valid GeoJSON Properties Test',
            description='Testing valid GeoJSON properties handling',
            geojson=json.dumps(valid_geojson_dict_original),
            observation_type='FO',
            user=self.user
        )
        lamning.save()

        retrieved_lamning = Lamning.objects.get(id=lamning.id)
        saved_geojson_dict = json.loads(retrieved_lamning.geojson)

        expected_saved_geojson_dict = {
            "type":"Feature",
            "geometry":{"type":"Point","coordinates":[13.5,60.5]},
            "properties":{}
        }
        self.assertEqual(saved_geojson_dict, expected_saved_geojson_dict)
        self.assertEqual(retrieved_lamning.center_lon, 13.5)
        self.assertEqual(retrieved_lamning.center_lat, 60.5)

    # --- New tests for Lamning.save() with stricter sanitization ---
    # The ones below are mostly from the previous iteration and should be correct.
    # I'll rename the one that was miscopied.

    def test_save_valid_feature_point_sanitized(self):
        """Test saving Lamning with a valid Point Feature gets sanitized as expected."""
        raw_geojson_dict = {
            "type": "Feature",
            "id": "should_be_removed",
            "bbox": [-10,-10,10,10],
            "geometry": {
                "type": "Point",
                "coordinates": [13.0, 60.0],
                "bbox": [-1, -1, 1, 1] # nested bbox also removed
            },
            "properties": {"name": "Original Name", "value": 123} # Should be emptied
        }
        lamning = Lamning.objects.create(
            title='Sanitized Point Lamning',
            description='Test save sanitization',
            geojson=json.dumps(raw_geojson_dict),
            observation_type='FO',
            user=self.user
        )
        # lamning.save() is called by create()

        retrieved = Lamning.objects.get(id=lamning.id)
        sanitized_geojson_stored = json.loads(retrieved.geojson)

        expected_geojson_dict = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [13.0, 60.0]},
            "properties": {} # Properties are emptied
        }
        self.assertEqual(sanitized_geojson_stored, expected_geojson_dict)
        self.assertEqual(retrieved.center_lon, 13.0)
        self.assertEqual(retrieved.center_lat, 60.0)

    def test_save_valid_feature_linestring_sanitized(self):
        raw_geojson_dict = {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[10,20],[30,40]]},
            "properties": {"name": "Original Line"}
        }
        lamning = Lamning.objects.create(
            title='Sanitized LineString Lamning',
            description='Test save sanitization line',
            geojson=json.dumps(raw_geojson_dict),
            observation_type='FO',
            user=self.user
        )
        retrieved = Lamning.objects.get(id=lamning.id)
        sanitized_geojson_stored = json.loads(retrieved.geojson)
        expected_geojson_dict = {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[10,20],[30,40]]},
            "properties": {}
        }
        self.assertEqual(sanitized_geojson_stored, expected_geojson_dict)
        # Centroid for LineString: ( (10+30)/2, (20+40)/2 ) = (20, 30)
        self.assertEqual(retrieved.center_lon, 20.0)
        self.assertEqual(retrieved.center_lat, 30.0)


    def test_save_valid_feature_polygon_sanitized(self):
        raw_geojson_dict = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[0,0],[10,0],[10,10],[0,10],[0,0]]]},
            "properties": {"name": "Original Polygon"}
        }
        lamning = Lamning.objects.create(
            title='Sanitized Polygon Lamning',
            description='Test save sanitization polygon',
            geojson=json.dumps(raw_geojson_dict),
            observation_type='FO',
            user=self.user
        )
        retrieved = Lamning.objects.get(id=lamning.id)
        sanitized_geojson_stored = json.loads(retrieved.geojson)
        expected_geojson_dict = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[0,0],[10,0],[10,10],[0,10],[0,0]]]},
            "properties": {}
        }
        self.assertEqual(sanitized_geojson_stored, expected_geojson_dict)
        # Centroid for Polygon: ( (0+10)/2, (0+10)/2 ) = (5, 5) for this simple square
        self.assertEqual(retrieved.center_lon, 5.0)
        self.assertEqual(retrieved.center_lat, 5.0)

    def test_save_malformed_json_string_raises_validation_error(self):
        malformed_json_str = '{"type": "Feature", "geometry": {"type": "Point", "coordinates": [1,1]' # Missing closing braces
        with self.assertRaises(ValidationError) as cm:
            Lamning.objects.create(
                title='Malformed JSON Test',
                description='Test save malformed',
                geojson=malformed_json_str,
                observation_type='FO',
                user=self.user
            )
        self.assertIn('geojson', cm.exception.error_dict)
        self.assertTrue("Invalid JSON" in cm.exception.error_dict['geojson'][0].message)


    def test_save_geojson_not_a_feature_raises_validation_error(self):
        not_a_feature_geojson_str = json.dumps({"type": "Point", "coordinates": [1,1]})
        with self.assertRaises(ValidationError) as cm:
            Lamning.objects.create(
                title='Not a Feature Test',
                description='Test save not a feature',
                geojson=not_a_feature_geojson_str,
                observation_type='FO',
                user=self.user
            )
        self.assertIn('geojson', cm.exception.error_dict)
        self.assertTrue("Input GeoJSON must be of type 'Feature'." in cm.exception.error_dict['geojson'][0].message)


    def test_save_feature_with_unsupported_geometry_type_raises_validation_error(self):
        unsupported_geom_geojson_str = json.dumps({
            "type": "Feature",
            "geometry": {"type": "MultiPolygon", "coordinates": []},
            "properties": {}
        })
        with self.assertRaises(ValidationError) as cm:
            Lamning.objects.create(
                title='Unsupported Geom Test',
                description='Test save unsupported geom',
                geojson=unsupported_geom_geojson_str,
                observation_type='FO',
                user=self.user
            )
        self.assertIn('geojson', cm.exception.error_dict)
        self.assertTrue("Geometry type must be one of" in cm.exception.error_dict['geojson'][0].message)
        self.assertTrue("Got 'MultiPolygon'." in cm.exception.error_dict['geojson'][0].message)

    def test_save_feature_with_invalid_coordinates_raises_validation_error(self):
        invalid_coords_geojson_str = json.dumps({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": "not_a_list"},
            "properties": {}
        })
        with self.assertRaises(ValidationError) as cm:
            Lamning.objects.create(
                title='Invalid Coords Test',
                description='Test save invalid coords',
                geojson=invalid_coords_geojson_str,
                observation_type='FO',
                user=self.user
            )
        self.assertIn('geojson', cm.exception.error_dict)
        self.assertTrue("Geometry type must be one of" in cm.exception.error_dict['geojson'][0].message) # Check specific message part
        self.assertTrue("Got 'MultiPolygon'." in cm.exception.error_dict['geojson'][0].message) # Check specific message part

    def test_save_feature_with_invalid_coordinates_raises_validation_error(self):
        invalid_coords_geojson_str = json.dumps({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": "this_is_not_a_list"}, # Invalid coordinate format
            "properties": {"name": "Invalid Coords"}
        })
        with self.assertRaises(ValidationError) as cm:
            Lamning.objects.create(
                title='Invalid Coords Save Test',
                description='Testing save with invalid coordinates in GeoJSON',
                geojson=invalid_coords_geojson_str,
                observation_type='FO',
                user=self.user
            )
        self.assertIn('geojson', cm.exception.error_dict)
        # Check for a message indicating coordinate validation failure from sanitize_geojson_object
        self.assertTrue("Point 'coordinates' must be a list" in cm.exception.error_dict['geojson'][0].message)
