import copy
import json # For constructing test inputs that might not be loadable by geojson library
from django.test import TestCase
from django.core.exceptions import ValidationError
import geojson # To create valid geojson objects for testing sanitize_geojson_object

from ...utilities import (
    centroid_from_feature,
    convert_geojson_to_schema_org,
    sanitize_geojson_object,
    validate_geojson,
)


class GeoJSONUtilTests(TestCase):
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
    """Tests the updated sanitize_geojson_object utility, assuming input has passed geojson.loads() and is_valid."""

    def _create_valid_input_feature_dict(self, geom_type, coordinates, feature_props=None, geom_props=None):
        """Helper to create a dict that would be the result of geojson.loads() for a valid Feature."""
        # geojson.loads() would produce dict-like objects. We simulate this with dicts.
        # The `is_valid` check would have passed.
        geom = {"type": geom_type, "coordinates": coordinates}
        if geom_props:
            geom.update(geom_props)

        feat = {"type": "Feature", "geometry": geom, "properties": feature_props if feature_props else {"name": "Test"}}
        # Add other foreign members to test their removal
        feat["id"] = "feat_id_1"
        feat["bbox"] = [-10, -10, 10, 10]
        feat["foreign_feature_prop"] = "should_be_removed"
        geom["foreign_geom_prop"] = "should_be_removed_from_geom"
        if geom_type != "Point": # bbox on geometry for non-points
             geom["bbox"] = [0,0,1,1]

        return feat


    def test_valid_feature_point_sanitized(self):
        # Input is a dictionary that mimics a valid Feature object parsed by geojson.loads()
        data = self._create_valid_input_feature_dict("Point", [10,20])

        expected = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [10, 20]},
            "properties": {}
        }
        self.assertEqual(sanitize_geojson_object(data), expected)

    def test_valid_feature_linestring_sanitized(self):
        data = self._create_valid_input_feature_dict("LineString", [[10,20],[30,40]])
        expected = {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[10,20],[30,40]]},
            "properties": {}
        }
        self.assertEqual(sanitize_geojson_object(data), expected)

    def test_valid_feature_polygon_sanitized(self):
        poly_coords = [[[0,0],[1,0],[1,1],[0,1],[0,0]]]
        data = self._create_valid_input_feature_dict("Polygon", poly_coords)
        expected = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": poly_coords},
            "properties": {}
        }
        self.assertEqual(sanitize_geojson_object(data), expected)

    def test_polygon_with_hole_sanitized(self):
        poly_coords_with_hole = [
            [[100.0, 0.0], [101.0, 0.0], [101.0, 1.0], [100.0, 1.0], [100.0, 0.0]],
            [[100.2, 0.2], [100.8, 0.2], [100.8, 0.8], [100.2, 0.8], [100.2, 0.2]]
        ]
        data = self._create_valid_input_feature_dict("Polygon", poly_coords_with_hole)
        expected = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": poly_coords_with_hole},
            "properties": {}
        }
        self.assertEqual(sanitize_geojson_object(data), expected)

    # --- Validation Error Tests for sanitize_geojson_object ---
    # These tests assume the input dictionary `data` has passed initial `geojson.loads().is_valid`
    # So, coordinate structures are assumed to be generally correct per GeoJSON spec,
    # but our function applies stricter rules (e.g. specific types, no FeatureCollections).

    def test_input_not_a_dictionary_still_raises_error(self):
        # Though Lamning.save() should pass a dict, this is a safeguard in the utility.
        with self.assertRaisesMessage(ValidationError, "Input must be a dictionary."):
            sanitize_geojson_object("not_a_dict_for_sure") # type: ignore

    def test_input_not_a_feature_raises_error(self):
        # Simulate a valid GeoJSON Point geometry object (not a Feature)
        data = geojson.Point((10,20)) # This is a geojson library object
        # Convert to dict for the function, as geojson.loads() might yield dicts
        # or custom objects that are dict-like. Our sanitize_geojson_object expects dict.
        data_dict = dict(data)
        with self.assertRaisesMessage(ValidationError, "Input GeoJSON must be of type 'Feature'."):
            sanitize_geojson_object(data_dict)

    def test_feature_missing_geometry_member_raises_error(self):
        data = {"type": "Feature", "properties": {}} # Missing 'geometry'
        with self.assertRaisesMessage(ValidationError, "Feature 'geometry' must be a dictionary."):
            sanitize_geojson_object(data)

    def test_feature_geometry_not_a_dict_raises_error(self):
        data = {"type": "Feature", "geometry": "not_a_dictionary", "properties": {}}
        with self.assertRaisesMessage(ValidationError, "Feature 'geometry' must be a dictionary."):
            sanitize_geojson_object(data)

    def test_unsupported_geometry_type_in_feature_raises_error(self):
        # Simulate a Feature with a MultiPoint geometry
        geom = geojson.MultiPoint([(10,20), (30,40)])
        data = geojson.Feature(geometry=geom, properties={"name":"test"})
        data_dict = dict(data) # Convert to dict
        # Manually ensure geometry is also a dict if needed by sanitize_geojson_object
        data_dict['geometry'] = dict(data_dict['geometry'])

        with self.assertRaisesMessage(ValidationError, "Geometry type must be one of ['Point', 'LineString', 'Polygon']. Got 'MultiPoint'."):
            sanitize_geojson_object(data_dict)

    def test_geometry_missing_coordinates_member_raises_error(self):
        # A dict that looks like a geometry but is missing coordinates
        # geojson.loads() + is_valid should catch this, but our function also double checks.
        data = {
            "type": "Feature",
            "geometry": {"type": "Point"}, # No 'coordinates' key
            "properties": {}
        }
        with self.assertRaisesMessage(ValidationError, "'coordinates' member is required for geometry type 'Point'."):
            sanitize_geojson_object(data)

    # Low-level coordinate validation tests (like wrong type in list, too few elements)
    # are now largely the responsibility of `geojson.loads().is_valid`.
    # sanitize_geojson_object assumes coordinates are structurally valid if they exist.
    # So, tests like test_point_invalid_coordinates_string, test_point_invalid_coordinates_too_few_elements, etc.
    # from the previous version of SanitizeGeoJSONObjectTest are removed as they would be caught by geojson.loads().

    def test_foreign_members_on_feature_are_stripped(self):
        data = self._create_valid_input_feature_dict("Point", [10,20])
        data["foreign_top_level"] = "should_be_gone"
        data["id"] = "test_id_feat" # Should be stripped
        data["bbox"] = [-1,-1,1,1] # Should be stripped

        expected = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [10, 20]},
            "properties": {}
        }
        self.assertEqual(sanitize_geojson_object(data), expected)

    def test_foreign_members_on_geometry_are_stripped(self):
        data = self._create_valid_input_feature_dict("Point", [10,20])
        # data['geometry'] is a dict after _create_valid_input_feature_dict
        data['geometry']['foreign_geom_prop'] = "also_gone"
        data['geometry']['bbox'] = [0,0,0,0] # Should be stripped

        expected = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [10, 20]}, # No foreign_geom_prop, no bbox
            "properties": {}
        }
        result = sanitize_geojson_object(data)
        self.assertEqual(result, expected)
        self.assertNotIn("foreign_geom_prop", result["geometry"])
        self.assertNotIn("bbox", result["geometry"])

    def test_valid_polygon_with_hole(self): # Renamed from previous test_polygon_valid_with_hole
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
