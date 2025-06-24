import copy
from django.test import TestCase

from ...utilities import (
    GEOJSON_ALLOWED_MEMBERS,  # Import for direct use in a test if needed
    centroid_from_feature,
    convert_geojson_to_schema_org,
    sanitize_geojson_object,
    validate_geojson,
)


class GeoJSONTest(TestCase):
    """Tests various GeoJSON utils"""

    def test_invalid_geojson(self):
        """Tests that invalid GeoJSON is rejected"""
        geo = '{"kladd": "kladd"}'
        self.assertEqual(validate_geojson(geo), False)

        geo = "pankakstårta"
        self.assertEqual(validate_geojson(geo), False)

    def test_centroid_from_geometry(self):
        """Tests that the centroid is calculated correctly from various geometries"""
        geo_polygon = '{"type":"Feature","properties":{},"geometry":{"type":"Polygon","coordinates":[[[-25.136719,38.134557],[5.625,54.775346],[49.746094,34.307144],[4.746094,23.079732],[-25.136719,38.134557]]]}}'
        self.assertEqual(centroid_from_feature(geo_polygon), (12.3046875, 38.927539))

        geo_point = '{"type":"Feature","properties":{},"geometry":{"type":"Point","coordinates":[-9.667969,49.382373]}}'
        self.assertEqual(centroid_from_feature(geo_point), (-9.667969, 49.382373))

    def test_schema_org_from_geojson(self):
        """Tests that the GeoJSON to schema.org conversion works"""

        geo_point = '{"type":"Feature","geometry":{"type":"Point","coordinates":[13.0743,60.5963]},"properties":null}'
        geo_point_result = {
            "@type": "schema:Place",
            "schema:geo": {
                "@type": "schema:GeoCoordinates",
                "schema:latitude": 60.5963,
                "schema:longitude": 13.0743,
            },
        }
        self.assertEqual(convert_geojson_to_schema_org(geo_point), geo_point_result)

        geo_line_string = '{"type":"Feature","geometry":{"type":"LineString","coordinates":[[17.000246506461547,58.73422091201479],[17.000272914559705,58.73434974847828],[17.000278196179337,58.73449777276221]]},"properties":null}'
        geo_line_result = {
            "@type": "schema:Place",
            "schema:geo": {
                "@type": "schema:GeoShape",
                "schema:line": "58.734221,17.000247 58.73435,17.000273 58.734498,17.000278",
            },
        }
        self.assertEqual(convert_geojson_to_schema_org(geo_line_string), geo_line_result)

        geo_polygon = '{"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[18.3857,57.6964],[18.3868,57.6981],[18.3892,57.6988],[18.3899,57.6986],[18.3891,57.6961],[18.3857,57.6964]]]},"properties":null}'
        geo_polygon_result = {
            "@type": "schema:Place",
            "schema:geo": {
                "@type": "schema:GeoShape",
                "schema:polygon": "57.6964,18.3857 57.6981,18.3868 57.6988,18.3892 57.6986,18.3899 57.6961,18.3891 57.6964,18.3857",
            },
        }
        self.assertEqual(convert_geojson_to_schema_org(geo_polygon), geo_polygon_result)


class GeoJSONSanitizationTest(TestCase):
    """Tests the sanitize_geojson_object utility."""

    def test_valid_point(self):
        point = {"type": "Point", "coordinates": [10, 20], "bbox": [-10, -20, 10, 20]}
        self.assertEqual(sanitize_geojson_object(copy.deepcopy(point)), point)

    def test_point_with_extra_member(self):
        point = {"type": "Point", "coordinates": [10, 20], "extra_member": "should_be_removed"}
        expected = {"type": "Point", "coordinates": [10, 20]}
        self.assertEqual(sanitize_geojson_object(point), expected)

    def test_valid_linestring(self):
        linestring = {"type": "LineString", "coordinates": [[10, 20], [30, 40]]}
        self.assertEqual(sanitize_geojson_object(copy.deepcopy(linestring)), linestring)

    def test_linestring_with_extra_member(self):
        linestring = {"type": "LineString", "coordinates": [[10, 20], [30, 40]], "foo": "bar"}
        expected = {"type": "LineString", "coordinates": [[10, 20], [30, 40]]}
        self.assertEqual(sanitize_geojson_object(linestring), expected)

    def test_valid_polygon(self):
        polygon = {"type": "Polygon", "coordinates": [[[10, 20], [30, 40], [50, 60], [10, 20]]]}
        self.assertEqual(sanitize_geojson_object(copy.deepcopy(polygon)), polygon)

    def test_polygon_with_extra_member(self):
        polygon = {"type": "Polygon", "coordinates": [[[10, 20], [30, 40], [50, 60], [10, 20]]], "baz": 123}
        expected = {"type": "Polygon", "coordinates": [[[10, 20], [30, 40], [50, 60], [10, 20]]]}
        self.assertEqual(sanitize_geojson_object(polygon), expected)

    def test_valid_multipoint(self):
        multipoint = {"type": "MultiPoint", "coordinates": [[10, 20], [30, 40]]}
        self.assertEqual(sanitize_geojson_object(copy.deepcopy(multipoint)), multipoint)

    def test_multipoint_with_extra_member(self):
        multipoint = {"type": "MultiPoint", "coordinates": [[10, 20], [30, 40]], "name": "points"}
        expected = {"type": "MultiPoint", "coordinates": [[10, 20], [30, 40]]}
        self.assertEqual(sanitize_geojson_object(multipoint), expected)

    def test_valid_multilinestring(self):
        multilinestring = {"type": "MultiLineString", "coordinates": [[[10, 20], [30, 40]]]}
        self.assertEqual(sanitize_geojson_object(copy.deepcopy(multilinestring)), multilinestring)

    def test_multilinestring_with_extra_member(self):
        multilinestring = {"type": "MultiLineString", "coordinates": [[[10, 20], [30, 40]]], "desc": "lines"}
        expected = {"type": "MultiLineString", "coordinates": [[[10, 20], [30, 40]]]}
        self.assertEqual(sanitize_geojson_object(multilinestring), expected)

    def test_valid_multipolygon(self):
        multipolygon = {"type": "MultiPolygon", "coordinates": [[[[10, 20], [30, 40], [50, 60], [10, 20]]]]}
        self.assertEqual(sanitize_geojson_object(copy.deepcopy(multipolygon)), multipolygon)

    def test_multipolygon_with_extra_member(self):
        multipolygon = {
            "type": "MultiPolygon",
            "coordinates": [[[[10, 20], [30, 40], [50, 60], [10, 20]]]],
            "area": 500,
        }
        expected = {"type": "MultiPolygon", "coordinates": [[[[10, 20], [30, 40], [50, 60], [10, 20]]]]}
        self.assertEqual(sanitize_geojson_object(multipolygon), expected)

    def test_valid_geometrycollection(self):
        geometrycollection = {
            "type": "GeometryCollection",
            "geometries": [{"type": "Point", "coordinates": [10, 20]}],
        }
        self.assertEqual(sanitize_geojson_object(copy.deepcopy(geometrycollection)), geometrycollection)

    def test_geometrycollection_with_extra_member(self):
        geometrycollection = {
            "type": "GeometryCollection",
            "geometries": [{"type": "Point", "coordinates": [10, 20]}],
            "collection_name": "my_geoms",
        }
        expected = {"type": "GeometryCollection", "geometries": [{"type": "Point", "coordinates": [10, 20]}]}
        # Need to sanitize the inner geometries too
        expected["geometries"][0] = sanitize_geojson_object(expected["geometries"][0])
        self.assertEqual(sanitize_geojson_object(geometrycollection), expected)

    def test_geometrycollection_with_extra_member_in_geometry(self):
        geometrycollection = {
            "type": "GeometryCollection",
            "geometries": [{"type": "Point", "coordinates": [10, 20], "geom_extra": "remove_me"}],
        }
        expected = {
            "type": "GeometryCollection",
            "geometries": [{"type": "Point", "coordinates": [10, 20]}],
        }
        self.assertEqual(sanitize_geojson_object(geometrycollection), expected)

    def test_valid_feature(self):
        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [10, 20]},
            "properties": {"name": "My Point", "value": 123},
            "id": "feat1",
            "bbox": [-1, -1, 1, 1]
        }
        self.assertEqual(sanitize_geojson_object(copy.deepcopy(feature)), feature)

    def test_feature_with_extra_member(self):
        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [10, 20]},
            "properties": {"name": "My Point"},
            "id": "feat1",
            "custom_field": "custom_value", # This should be removed
        }
        expected = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [10, 20]},
            "properties": {"name": "My Point"},
            "id": "feat1",
        }
        self.assertEqual(sanitize_geojson_object(feature), expected)

    def test_feature_with_null_geometry(self):
        feature = {"type": "Feature", "geometry": None, "properties": {"name": "Unlocated"}}
        self.assertEqual(sanitize_geojson_object(copy.deepcopy(feature)), feature)

    def test_feature_properties_untouched(self):
        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [10, 20]},
            "properties": {"name": "My Point", "nested_prop": {"a": 1, "b": [1,2,3]}, "is_valid": True},
        }
        # Properties should remain exactly as they are
        self.assertEqual(sanitize_geojson_object(copy.deepcopy(feature)), feature)

    def test_feature_with_extra_in_geometry(self):
        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [10, 20], "geom_extra": "remove"},
            "properties": {"name": "My Point"},
        }
        expected = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [10, 20]},
            "properties": {"name": "My Point"},
        }
        self.assertEqual(sanitize_geojson_object(feature), expected)


    def test_valid_featurecollection(self):
        featurecollection = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [10, 20]},
                    "properties": {"name": "Point 1"},
                }
            ],
            "bbox": [0,0,10,20]
        }
        self.assertEqual(sanitize_geojson_object(copy.deepcopy(featurecollection)), featurecollection)

    def test_featurecollection_with_extra_member(self):
        featurecollection = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [10, 20]},
                    "properties": {"name": "Point 1"},
                }
            ],
            "collection_info": "some_info", # remove this
        }
        expected = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [10, 20]},
                    "properties": {"name": "Point 1"},
                }
            ],
        }
        self.assertEqual(sanitize_geojson_object(featurecollection), expected)

    def test_featurecollection_with_extra_in_feature(self):
        featurecollection = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [10, 20]},
                    "properties": {"name": "Point 1"},
                    "feature_extra": "remove_this_too",
                }
            ],
        }
        expected = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [10, 20]},
                    "properties": {"name": "Point 1"},
                }
            ],
        }
        self.assertEqual(sanitize_geojson_object(featurecollection), expected)

    def test_featurecollection_with_extra_in_feature_geometry(self):
        featurecollection = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [10, 20], "geom_extra": "remove_me"},
                    "properties": {"name": "Point 1"},
                }
            ],
        }
        expected = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [10, 20]},
                    "properties": {"name": "Point 1"},
                }
            ],
        }
        self.assertEqual(sanitize_geojson_object(featurecollection), expected)

    def test_empty_featurecollection_features_array(self):
        data = {"type": "FeatureCollection", "features": []}
        self.assertEqual(sanitize_geojson_object(copy.deepcopy(data)), data)

    def test_empty_geometrycollection_geometries_array(self):
        data = {"type": "GeometryCollection", "geometries": []}
        self.assertEqual(sanitize_geojson_object(copy.deepcopy(data)), data)

    def test_non_geojson_dict_returned_as_is(self):
        data = {"not_a_type": "some_value", "key": "value"}
        self.assertEqual(sanitize_geojson_object(copy.deepcopy(data)), data)

    def test_non_dict_input_returned_as_is(self):
        data_list = [{"type": "Point", "coordinates": [1, 1]}]
        self.assertEqual(sanitize_geojson_object(copy.deepcopy(data_list)), data_list) # type: ignore
        data_str = '{"type": "Point", "coordinates": [1, 1]}'
        self.assertEqual(sanitize_geojson_object(copy.deepcopy(data_str)), data_str) # type: ignore

    def test_unknown_geojson_type(self):
        # If a "type" is present but not in our known list, it should only keep common members.
        data = {"type": "SuperDuperGeometry", "coordinates": [1, 2, 3], "custom": "field"}
        expected = {"type": "SuperDuperGeometry"} # No bbox in original
        self.assertEqual(sanitize_geojson_object(data), expected)

        data_with_bbox = {"type": "SuperDuperGeometry", "coordinates": [1, 2, 3], "custom": "field", "bbox": [0,0,1,1]}
        expected_with_bbox = {"type": "SuperDuperGeometry", "bbox": [0,0,1,1]}
        self.assertEqual(sanitize_geojson_object(data_with_bbox), expected_with_bbox)

    def test_bbox_preserved_for_all_types(self):
        types_with_coords = ["Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon"]
        for geo_type in types_with_coords:
            obj = {"type": geo_type, "coordinates": [], "bbox": [0,0,1,1], "extra": "remove"}
            expected = {"type": geo_type, "coordinates": [], "bbox": [0,0,1,1]}
            self.assertEqual(sanitize_geojson_object(obj), expected, f"Failed for {geo_type}")

        gc = {"type": "GeometryCollection", "geometries": [], "bbox": [0,0,1,1], "extra": "remove"}
        expected_gc = {"type": "GeometryCollection", "geometries": [], "bbox": [0,0,1,1]}
        self.assertEqual(sanitize_geojson_object(gc), expected_gc, "Failed for GeometryCollection")

        feat = {"type": "Feature", "geometry": None, "properties": {}, "bbox": [0,0,1,1], "extra": "remove"}
        expected_feat = {"type": "Feature", "geometry": None, "properties": {}, "bbox": [0,0,1,1]}
        self.assertEqual(sanitize_geojson_object(feat), expected_feat, "Failed for Feature")

        fc = {"type": "FeatureCollection", "features": [], "bbox": [0,0,1,1], "extra": "remove"}
        expected_fc = {"type": "FeatureCollection", "features": [], "bbox": [0,0,1,1]}
        self.assertEqual(sanitize_geojson_object(fc), expected_fc, "Failed for FeatureCollection")

    def test_nested_structure_complex(self):
        complex_fc = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": "f1",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[ [0,0],[1,0],[1,1],[0,1],[0,0] ]],
                        "poly_extra": "gone"
                    },
                    "properties": {"name": "Polygon Feature", "data": {"value": 1, "nested_extra": "stay"}},
                    "feature_extra": "gone too"
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "GeometryCollection",
                        "geometries": [
                            {"type": "Point", "coordinates": [2,2], "point_extra": "gone"},
                            {"type": "LineString", "coordinates": [[3,3],[4,4]], "ls_extra": "gone"}
                        ],
                        "gc_extra": "gone"
                    },
                    "properties": {"description": "GC feature"}
                }
            ],
            "fc_extra": "gone",
            "bbox": [0,0,4,4]
        }

        expected_fc = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": "f1",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[ [0,0],[1,0],[1,1],[0,1],[0,0] ]],
                    },
                    "properties": {"name": "Polygon Feature", "data": {"value": 1, "nested_extra": "stay"}}
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "GeometryCollection",
                        "geometries": [
                            {"type": "Point", "coordinates": [2,2]},
                            {"type": "LineString", "coordinates": [[3,3],[4,4]]}
                        ]
                    },
                    "properties": {"description": "GC feature"}
                }
            ],
            "bbox": [0,0,4,4]
        }
        self.assertEqual(sanitize_geojson_object(complex_fc), expected_fc)
