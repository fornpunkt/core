import copy
from django.test import TestCase
from django.core.exceptions import ValidationError

from ...utilities import (
    # GEOJSON_ALLOWED_MEMBERS, # No longer needed directly in tests for sanitize_geojson_object
    centroid_from_feature, # Keep if other tests use it
    convert_geojson_to_schema_org, # Keep if other tests use it
    sanitize_geojson_object,
    validate_geojson, # Keep if other tests use it
)


class GeoJSONUtilTests(TestCase): # Renamed from GeoJSONTest to avoid conflict if old class name was used by test runner
    """Tests various original GeoJSON utils, excluding the old sanitize_geojson_object tests."""

    def test_invalid_geojson(self):
        """Tests that invalid GeoJSON is rejected by validate_geojson."""
        geo = '{"kladd": "kladd"}' # Not valid GeoJSON structure
        self.assertEqual(validate_geojson(geo), False)

        geo = "pankakstårta" # Not JSON
        self.assertEqual(validate_geojson(geo), False)

        geo_valid_json_not_geojson = '{"name": "test"}' # Valid JSON, but not GeoJSON
        self.assertEqual(validate_geojson(geo_valid_json_not_geojson), False)


    def test_centroid_from_geometry(self):
        """Tests that the centroid is calculated correctly from various geometries."""
        # This test uses a Feature string, which is what centroid_from_feature expects
        geo_polygon_feature_str = '{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[-25.136719,38.134557],[5.625,54.775346],[49.746094,34.307144],[4.746094,23.079732],[-25.136719,38.134557]]]}}'
        self.assertEqual(centroid_from_feature(geo_polygon_feature_str), (12.3046875, 38.927539))

        geo_point_feature_str = '{"type":"Feature","properties":{},"geometry":{"type":"Point","coordinates":[-9.667969,49.382373]}}'
        self.assertEqual(centroid_from_feature(geo_point_feature_str), (-9.667969, 49.382373))

    def test_schema_org_from_geojson(self):
        """Tests that the GeoJSON to schema.org conversion works."""
        # These tests also use Feature strings
        geo_point_feature_str = '{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]},"properties":null}'
        geo_point_result = {
            "@type": "schema:Place",
            "schema:geo": {
                "@type": "schema:GeoCoordinates",
                "schema:latitude": 60.5963,
                "schema:longitude": 13.0743,
            },
        }
        self.assertEqual(convert_geojson_to_schema_org(geo_point_feature_str), geo_point_result)

        geo_line_string_feature_str = '{"type":"Feature","geometry":{"type":"LineString","coordinates":[[17.000246506461547,58.73422091201479],[17.000272914559705,58.73434974847828],[17.000278196179337,58.73449777276221]]},"properties":null}'
        geo_line_result = {
            "@type": "schema:Place",
            "schema:geo": {
                "@type": "schema:GeoShape",
                "schema:line": "58.734221,17.000247 58.73435,17.000273 58.734498,17.000278",
            },
        }
        self.assertEqual(convert_geojson_to_schema_org(geo_line_string_feature_str), geo_line_result)

        geo_polygon_feature_str = '{"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[18.3857,57.6964],[18.3868,57.6981],[18.3892,57.6988],[18.3899,57.6986],[18.3891,57.6961],[18.3857,57.6964]]]},"properties":null}'
        geo_polygon_result = {
            "@type": "schema:Place",
            "schema:geo": {
                "@type": "schema:GeoShape",
                "schema:polygon": "57.6964,18.3857 57.6981,18.3868 57.6988,18.3892 57.6986,18.3899 57.6961,18.3891 57.6964,18.3857",
            },
        }
        self.assertEqual(convert_geojson_to_schema_org(geo_polygon_feature_str), geo_polygon_result)

# This is the new test class for the current sanitize_geojson_object function.
# The old GeoJSONSanitizationTest class has been removed.
class SanitizeGeoJSONObjectTest(TestCase):
    """Tests the updated sanitize_geojson_object utility."""

    def test_valid_feature_point(self):
        data = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [10, 20], "bbox": [9,19,11,21]},
            "properties": {"name": "Test Point", "value": 123},
            "id": "feat1",
            "bbox": [9,19,11,21],
            "custom_prop": "remove"
        }
        expected = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [10, 20]},
            "properties": {}
        }
        self.assertEqual(sanitize_geojson_object(data), expected)

    def test_valid_feature_linestring(self):
        data = {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[10,20],[30,40]]},
            "properties": {"name": "Test Line"},
            "id": "ls1"
        }
        expected = {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[10,20],[30,40]]},
            "properties": {}
        }
        self.assertEqual(sanitize_geojson_object(data), expected)

    def test_valid_feature_polygon(self):
        data = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[0,0],[1,0],[1,1],[0,1],[0,0]]]},
            "properties": {"name": "Test Polygon"}
        }
        expected = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[0,0],[1,0],[1,1],[0,1],[0,0]]]},
            "properties": {}
        }
        self.assertEqual(sanitize_geojson_object(data), expected)

    def test_geometry_has_foreign_members_stripped(self):
        data = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [10, 20], "custom_geom_prop": "remove_me"},
            "properties": {"name": "Test"}
        }
        expected = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [10, 20]},
            "properties": {}
        }
        self.assertEqual(sanitize_geojson_object(data), expected)

    # --- Validation Error Tests ---

    def test_input_not_a_dictionary(self):
        with self.assertRaisesMessage(ValidationError, "Input must be a dictionary."):
            sanitize_geojson_object("not_a_dict") # type: ignore

    def test_input_not_a_feature(self):
        data = {"type": "Point", "coordinates": [10, 20]} # A geometry, not a feature
        with self.assertRaisesMessage(ValidationError, "Input GeoJSON must be of type 'Feature'."):
            sanitize_geojson_object(data)

    def test_feature_missing_geometry(self):
        data = {"type": "Feature", "properties": {}}
        with self.assertRaisesMessage(ValidationError, "Feature 'geometry' must be a dictionary."):
            sanitize_geojson_object(data)

    def test_feature_geometry_not_a_dict(self):
        data = {"type": "Feature", "geometry": "not_a_dict", "properties": {}}
        with self.assertRaisesMessage(ValidationError, "Feature 'geometry' must be a dictionary."):
            sanitize_geojson_object(data)

    def test_unsupported_geometry_type(self):
        data = {
            "type": "Feature",
            "geometry": {"type": "MultiPoint", "coordinates": [[10, 20]]},
            "properties": {}
        }
        with self.assertRaisesMessage(ValidationError, "Geometry type must be one of ['Point', 'LineString', 'Polygon']. Got 'MultiPoint'."):
            sanitize_geojson_object(data)

    def test_geometry_missing_coordinates(self):
        data = {
            "type": "Feature",
            "geometry": {"type": "Point"}, # Missing coordinates
            "properties": {}
        }
        with self.assertRaisesMessage(ValidationError, "'coordinates' member is required for geometry type 'Point'."):
            sanitize_geojson_object(data)

    def test_point_invalid_coordinates_string(self):
        data = {"type":"Feature", "geometry": {"type":"Point", "coordinates": "10,20"}, "properties":{}}
        with self.assertRaisesMessage(ValidationError, "Point 'coordinates' must be a list of 2 or 3 numbers."):
            sanitize_geojson_object(data)

    def test_point_invalid_coordinates_too_few_elements(self):
        data = {"type":"Feature", "geometry": {"type":"Point", "coordinates": [10]}, "properties":{}}
        with self.assertRaisesMessage(ValidationError, "Point 'coordinates' must be a list of 2 or 3 numbers."):
            sanitize_geojson_object(data)

    def test_point_invalid_coordinates_too_many_elements(self):
        data = {"type":"Feature", "geometry": {"type":"Point", "coordinates": [10,20,30,40]}, "properties":{}}
        with self.assertRaisesMessage(ValidationError, "Point 'coordinates' must be a list of 2 or 3 numbers."):
            sanitize_geojson_object(data)

    def test_point_invalid_coordinates_wrong_type(self):
        data = {"type":"Feature", "geometry": {"type":"Point", "coordinates": [10,"20"]}, "properties":{}}
        with self.assertRaisesMessage(ValidationError, "Point 'coordinates' must be a list of 2 or 3 numbers."):
            sanitize_geojson_object(data)

    def test_linestring_invalid_coordinates_not_list_of_lists(self):
        data = {"type":"Feature", "geometry": {"type":"LineString", "coordinates": [10,20,30,40]}, "properties":{}}
        with self.assertRaisesMessage(ValidationError, "LineString 'coordinates' must be a list of 2 or more positions (each a list of 2-3 numbers)."):
            sanitize_geojson_object(data)

    def test_linestring_invalid_coordinates_too_few_points(self):
        data = {"type":"Feature", "geometry": {"type":"LineString", "coordinates": [[10,20]]}, "properties":{}} # Needs >= 2 points
        with self.assertRaisesMessage(ValidationError, "LineString 'coordinates' must be a list of 2 or more positions (each a list of 2-3 numbers)."):
            sanitize_geojson_object(data)

    def test_linestring_invalid_coordinates_point_wrong_type(self):
        data = {"type":"Feature", "geometry": {"type":"LineString", "coordinates": [[10,20], [30,"40"]]}, "properties":{}}
        with self.assertRaisesMessage(ValidationError, "LineString 'coordinates' must be a list of 2 or more positions (each a list of 2-3 numbers)."):
            sanitize_geojson_object(data)

    def test_polygon_invalid_coordinates_not_list_of_lists_of_lists(self):
        data = {"type":"Feature", "geometry": {"type":"Polygon", "coordinates": [[10,20],[30,40]]}, "properties":{}}
        with self.assertRaisesMessage(ValidationError, "Polygon 'coordinates' must be a list of linear rings (each a list of positions)."):
            sanitize_geojson_object(data)

    def test_polygon_empty_coordinates_list(self): # An empty list of rings
        data = {"type":"Feature", "geometry": {"type":"Polygon", "coordinates": []}, "properties":{}}
        with self.assertRaisesMessage(ValidationError, "Polygon 'coordinates' must be a list of linear rings (each a list of positions)."): # Fails because _is_valid_coordinate_list expects non-empty for depth 3 unless min_depth=0
            sanitize_geojson_object(data)

    def test_polygon_ring_too_few_points(self):
        data = {"type":"Feature", "geometry": {"type":"Polygon", "coordinates": [[[0,0],[1,0],[0,0]]]}, "properties":{}} # Ring needs >= 4 points
        with self.assertRaisesMessage(ValidationError, "Each ring in a Polygon must have at least 4 positions."):
            sanitize_geojson_object(data)

    def test_polygon_ring_not_closed(self):
        data = {"type":"Feature", "geometry": {"type":"Polygon", "coordinates": [[[0,0],[1,0],[1,1],[0,1]]]}, "properties":{}} # Not closed
        with self.assertRaisesMessage(ValidationError, "The first and last positions in a Polygon ring must be identical."):
            sanitize_geojson_object(data)

    def test_polygon_valid_with_hole(self): # Ensure complex but valid polygon is fine
        data = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[100.0, 0.0], [101.0, 0.0], [101.0, 1.0], [100.0, 1.0], [100.0, 0.0]], # Exterior
                    [[100.2, 0.2], [100.8, 0.2], [100.8, 0.8], [100.2, 0.8], [100.2, 0.2]]  # Interior (hole)
                ]
            },
            "properties": {"name": "Poly with hole"}
        }
        expected = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [[100.0, 0.0], [101.0, 0.0], [101.0, 1.0], [100.0, 1.0], [100.0, 0.0]],
                    [[100.2, 0.2], [100.8, 0.2], [100.8, 0.8], [100.2, 0.8], [100.2, 0.2]]
                ]
            },
            "properties": {}
        }
        self.assertEqual(sanitize_geojson_object(data), expected)
