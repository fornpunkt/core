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
    # The tests like test_geojson_sanitization_extra_top_level_properties,
    # test_geojson_sanitization_extra_nested_properties_in_geometry, and
    # test_geojson_valid_geojson_unchanged_except_properties_and_allowed_keys
    # are effectively replaced by the more specific `test_save_valid_feature_..._sanitized` tests.
    # I will remove the "Existing tests adapted..." section to avoid redundancy and use the clearer named tests.

    def test_geojson_empty_string_is_invalid_on_full_clean(self): # Renamed for clarity
        """Test that an empty GeoJSON string fails model validation via full_clean()."""
        lamning_empty_str = Lamning(
            title='Empty String GeoJSON',
            description='Test for empty geojson string',
            geojson="",
            observation_type='FO',
            user=self.user
        )
        with self.assertRaises(ValidationError) as cm:
            lamning_empty_str.full_clean() # full_clean calls model's clean_fields, then clean, then validators
        self.assertIn('geojson', cm.exception.error_dict)
        # The error can come from TextField(blank=False) or the save method's initial check if save is forced.
        # For full_clean, it's likely from clean_fields due to blank=False.

    def test_geojson_none_value_is_invalid_on_full_clean(self): # Renamed for clarity
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
        self.assertIn('geojson', cm.exception.error_dict)


    # --- Tests for Lamning.save() focusing on the new sanitization and validation flow ---

    def test_save_valid_feature_point_is_correctly_sanitized(self): # Renamed for clarity
        """Test saving Lamning with a valid Point Feature gets correctly sanitized."""
        raw_geojson_dict = {
            "type": "Feature",
            "id": "should_be_removed",
            "bbox": [-10,-10,10,10], # Feature bbox
            "geometry": {
                "type": "Point",
                "coordinates": [13.0, 60.0],
                "bbox": [-1, -1, 1, 1] # Geometry bbox
            },
            "properties": {"name": "Original Name", "value": 123}, # Should be emptied
            "foreign_prop": "remove_me"
        }
        lamning = Lamning.objects.create( # .create() calls .save()
            title='Sanitized Point Lamning',
            description='Test save sanitization',
            geojson=json.dumps(raw_geojson_dict),
            observation_type='FO',
            user=self.user
        )
        retrieved = Lamning.objects.get(id=lamning.id)
        sanitized_geojson_stored = json.loads(retrieved.geojson)

        expected_geojson_dict = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [13.0, 60.0]}, # geometry bbox removed
            "properties": {} # Properties emptied, id/bbox/foreign_prop from Feature removed
        }
        self.assertEqual(sanitized_geojson_stored, expected_geojson_dict)
        self.assertEqual(retrieved.center_lon, 13.0)
        self.assertEqual(retrieved.center_lat, 60.0)

    def test_save_valid_feature_linestring_is_correctly_sanitized(self): # Renamed
        raw_geojson_dict = {
            "type": "Feature",
            "id": "ls001",
            "geometry": {"type": "LineString", "coordinates": [[10,20],[30,40]]},
            "properties": {"name": "Original Line", "length": 100}
        }
        lamning = Lamning.objects.create(
            title='Sanitized LineString Lamning',
            geojson=json.dumps(raw_geojson_dict),
            user=self.user, description=""
        )
        retrieved = Lamning.objects.get(id=lamning.id)
        sanitized_geojson_stored = json.loads(retrieved.geojson)
        expected_geojson_dict = {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[10,20],[30,40]]},
            "properties": {}
        }
        self.assertEqual(sanitized_geojson_stored, expected_geojson_dict)
        self.assertEqual(retrieved.center_lon, 20.0)
        self.assertEqual(retrieved.center_lat, 30.0)


    def test_save_valid_feature_polygon_is_correctly_sanitized(self): # Renamed
        raw_geojson_dict = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[0,0],[10,0],[10,10],[0,10],[0,0]]]},
            "properties": {"name": "Original Polygon", "area": 100}
        }
        lamning = Lamning.objects.create(
            title='Sanitized Polygon Lamning',
            geojson=json.dumps(raw_geojson_dict),
            user=self.user, description=""
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
        self.assertIn('geojson', cm.exception.message_dict)
        self.assertTrue("Invalid GeoJSON string" in cm.exception.message_dict['geojson'][0])


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

    # The test_save_feature_with_invalid_coordinates_raises_validation_error below is the correct one.
    # The one above with the same name had incorrect assertions.
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
        self.assertIn('geojson', cm.exception.message_dict)
        error_message = cm.exception.message_dict['geojson'][0]
        self.assertTrue("Invalid GeoJSON string" in error_message)
        # Check for part of the original ValueError message from the geojson library
        self.assertTrue("not a JSON compliant number" in error_message or "coordinates must be a list or tuple" in error_message)
