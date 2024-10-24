from django.test import TestCase

from ...utilities import centroid_from_feature, convert_geojson_to_schema_org, validate_geojson


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
