import json
from json.decoder import JSONDecodeError
from urllib.parse import ParseResult, parse_qs, urlencode, urlparse
from uuid import UUID

import geojson
import sentry_sdk as sentry
import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import Http404
from django.http.response import JsonResponse
from hashids import Hashids
from taggit.utils import _parse_tags

hashids = Hashids(settings.HASHIDS_SALT, min_length=7)

# --- GeoJSON Sanitization Constants ---
# Based on RFC 7946: https://www.rfc-editor.org/rfc/rfc7946
# These sets define the ALLOWED top-level members for each GeoJSON object type.
# The 'type' member is implicitly required for all.

# Defines allowed members for the specific GeoJSON types we support for Lamning.
# `bbox` is disallowed. `id` is disallowed on Features.
# `properties` on Features will be emptied, but the key itself is allowed.
GEOJSON_ALLOWED_MEMBERS = {
    "Feature": {"type", "geometry", "properties"},
    "Point": {"type", "coordinates"},
    "LineString": {"type", "coordinates"},
    "Polygon": {"type", "coordinates"},
}
# --- End GeoJSON Sanitization Constants ---


def _is_valid_coordinate_list(coords, min_depth=1, max_depth=1, item_type=float, min_len=2, max_len=3):
    """Helper to check if a list is a valid coordinate or list of coordinates."""
    if not isinstance(coords, list):
        return False
    if not coords and min_depth > 0 : # allow empty list if min_depth is 0 (e.g. empty list of rings for polygon)
        return False

    if min_depth == 0 and not coords: # Specific case for Polygon coordinates: list of rings, can be empty if no holes
        return True


    current_depth = 0
    q = [coords]

    # Determine actual depth and structure
    temp_coords = coords
    while isinstance(temp_coords, list) and temp_coords:
        current_depth += 1
        if not temp_coords: # Empty list at current depth
            break
        temp_coords = temp_coords[0]

    if not (min_depth <= current_depth <= max_depth):
        return False

    # Validate items at the deepest level
    if current_depth == 1: # e.g. Point coordinates [1.0, 2.0]
        if not (min_len <= len(coords) <= max_len): return False
        return all(isinstance(c, (int, float)) for c in coords)
    if current_depth == 2: # e.g. LineString coordinates [[1.0,2.0], [3.0,4.0]]
        return all(
            isinstance(pos, list) and
            (min_len <= len(pos) <= max_len) and
            all(isinstance(c, (int, float)) for c in pos)
            for pos in coords
        )
    if current_depth == 3: # e.g. Polygon coordinates [[[1.0,2.0], ...]]
         return all(
            isinstance(ring, list) and all(
                isinstance(pos, list) and
                (min_len <= len(pos) <= max_len) and
                all(isinstance(c, (int, float)) for c in pos)
                for pos in ring
            )
            for ring in coords
        )
    return False


def sanitize_geojson_object(data: dict) -> dict:
    """
    Sanitizes and validates a GeoJSON Feature object dictionary.
    It ensures the Feature contains a supported geometry (Point, LineString, Polygon),
    empties the 'properties' field, and removes any non-standard members or 'bbox'/'id'.

    Raises ValidationError if the input is not a valid Feature object according
    to the specified strict rules.
    """
    if not isinstance(data, dict):
        raise ValidationError("Input must be a dictionary.")

    if data.get("type") != "Feature":
        raise ValidationError("Input GeoJSON must be of type 'Feature'.")

    sanitized_feature = {"type": "Feature"}

    # Properties must be an empty dictionary
    sanitized_feature["properties"] = {}

    # Validate and sanitize geometry
    original_geometry = data.get("geometry")
    if not isinstance(original_geometry, dict):
        raise ValidationError("Feature 'geometry' must be a dictionary.")

    geom_type = original_geometry.get("type")
    allowed_geom_types = ["Point", "LineString", "Polygon"]
    if geom_type not in allowed_geom_types:
        raise ValidationError(f"Geometry type must be one of {allowed_geom_types}. Got '{geom_type}'.")

    sanitized_geometry = {"type": geom_type}

    original_coordinates = original_geometry.get("coordinates")
    if original_coordinates is None: # Explicit None check, as empty list might be valid for some scenarios (not Point)
         raise ValidationError(f"'coordinates' member is required for geometry type '{geom_type}'.")


    # Basic coordinate structure validation
    if geom_type == "Point":
        if not _is_valid_coordinate_list(original_coordinates, min_depth=1, max_depth=1, item_type=(int, float), min_len=2, max_len=3):
            raise ValidationError("Point 'coordinates' must be a list of 2 or 3 numbers.")
    elif geom_type == "LineString":
        if not _is_valid_coordinate_list(original_coordinates, min_depth=2, max_depth=2, item_type=(int,float), min_len=2, max_len=3) or len(original_coordinates) < 2:
            raise ValidationError("LineString 'coordinates' must be a list of 2 or more positions (each a list of 2-3 numbers).")
    elif geom_type == "Polygon":
        # Each ring must have at least 4 positions, first and last same.
        # _is_valid_coordinate_list checks structure, then we add specific Polygon rules.
        if not _is_valid_coordinate_list(original_coordinates, min_depth=3, max_depth=3, item_type=(int,float), min_len=2, max_len=3) or not original_coordinates:
            raise ValidationError("Polygon 'coordinates' must be a list of linear rings (each a list of positions).")
        for ring in original_coordinates:
            if not isinstance(ring, list) or len(ring) < 4:
                raise ValidationError("Each ring in a Polygon must have at least 4 positions.")
            if ring[0] != ring[-1]:
                raise ValidationError("The first and last positions in a Polygon ring must be identical.")

    sanitized_geometry["coordinates"] = original_coordinates # Already validated

    # Remove any other foreign properties from the geometry object
    final_sanitized_geometry = {}
    allowed_geom_keys = GEOJSON_ALLOWED_MEMBERS.get(geom_type, set())
    for k, v in sanitized_geometry.items():
        if k in allowed_geom_keys:
            final_sanitized_geometry[k] = v

    sanitized_feature["geometry"] = final_sanitized_geometry

    # Only keep allowed top-level keys for the Feature itself
    final_sanitized_feature = {}
    allowed_feature_keys = GEOJSON_ALLOWED_MEMBERS.get("Feature", set())
    for k,v in sanitized_feature.items():
        if k in allowed_feature_keys:
            final_sanitized_feature[k] = v

    return final_sanitized_feature


def h_encode(identifier):
    return hashids.encode(identifier)


def h_decode(hash_identifier):
    z = hashids.decode(hash_identifier)
    if z:
        return z[0]
    # this ensures that a string is always returned to things like Generic detail views
    # so if a given identifier can't be decoded it will still return a string althrough it wont be resolved in the db
    # this is to prevent errors when trying to resolve a non-existing identifier such as lowercase versions of our urls
    else:
        return "404-not-found"


class HashIdConverter:
    regex = "[a-zA-Z0-9]{7,}"

    def to_python(self, value):
        return h_decode(value)

    def to_url(self, value):
        return h_encode(value)


def replace_url_parameter(url, key, value):
    """Replace a parameter in a url."""
    (scheme, netloc, path, params, query, fragment) = urlparse(url)
    query_dict = parse_qs(query)
    query_dict[key] = value
    query = urlencode(query_dict, doseq=True)
    return ParseResult(scheme, netloc, path, params, query, fragment).geturl()


class JsonApiResponse(JsonResponse):
    def __init__(self, *args, content_type="application/json", json_dumps_params=None, **kwargs):
        json_dumps_params = {"ensure_ascii": False, **(json_dumps_params or {})}
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS, HEAD",
        }

        kwargs.setdefault("headers", headers)

        super().__init__(*args, json_dumps_params=json_dumps_params, content_type=content_type, safe=False, **kwargs)


def validate_observation_type(observation_type: str) -> bool:
    """Validates an observation type."""
    if observation_type in ["FO", "RO", "MO"]:
        return True

    raise ValidationError("Otillåten observationstyp. Tillåtna värden är FO och RO.")


def validate_geojson(geojson_data: str) -> bool:
    """GeoJSON validation by loading it."""
    try:
        data = geojson.loads(geojson_data)
    except JSONDecodeError:
        return False

    # non geojson input won't get the valid attribute
    try:
        if not data.is_valid:
            return False
    except AttributeError:
        return False

    return True


def centroid_from_feature(geojson_data: str) -> tuple:
    """Given a GeoJSON feature this function tries to create a centroid."""
    data = geojson.loads(geojson_data)
    coords = list(geojson.utils.coords(data))
    if len(coords) == 1:
        return coords[0]
    else:
        # poor mans centroid
        lons = [t[0] for t in coords]
        max_lon = max(lons)
        min_lon = min(lons)
        c_lon = min_lon + (abs(min_lon - max_lon) / 2)
        lats = [t[1] for t in coords]
        max_lat = max(lats)
        min_lat = min(lats)
        c_lat = min_lat + (abs(min_lat - max_lat) / 2)

        return tuple((round(c_lon, 8), round(c_lat, 8)))


def convert_geojson_to_schema_org(geojson_data: str) -> dict:
    """Converts GeoJSON to Schema.org"""
    parsed_geojson = geojson.loads(geojson_data)
    geo_type = parsed_geojson.geometry.type
    if geo_type == "Point":
        return {
            "@type": "schema:Place",
            "schema:geo": {
                "@type": "schema:GeoCoordinates",
                "schema:latitude": parsed_geojson.geometry.coordinates[1],
                "schema:longitude": parsed_geojson.geometry.coordinates[0],
            },
        }
    elif geo_type == "LineString":
        space_seperated_coords = " ".join(f"{c[1]},{c[0]}" for c in parsed_geojson.geometry.coordinates)
        return {
            "@type": "schema:Place",
            "schema:geo": {
                "@type": "schema:GeoShape",
                "schema:line": space_seperated_coords,
            },
        }
    else:
        space_seperated_coords = " ".join(f"{c[1]},{c[0]}" for c in parsed_geojson.geometry.coordinates[0])
        return {
            "@type": "schema:Place",
            "schema:geo": {
                "@type": "schema:GeoShape",
                "schema:polygon": space_seperated_coords,
            },
        }


def is_possible_raa_id(identifier: str):
    """Checks if the given string is a version 4 UUID to ensure that it can be a KMR lamning"""
    try:
        uuid_version = UUID(identifier).version
    except ValueError:
        return False
    if uuid_version == 4:
        return True
    return False


def is_raa_id(identifier: str):
    """Checks if a given string is a UUID used by RAÄ by issuing a HTTP HEAD request to kulturarvsdata.se"""
    if not is_possible_raa_id(identifier):
        return False
    try:
        r = requests.head(f"https://kulturarvsdata.se/raa/lamning/{identifier}")
    except requests.exceptions.ConnectionError:
        return False
    if r.status_code == 200:
        return True
    return False


def create_meta_description(description: str) -> str:
    """Ensures a string is no longer than 150, so that it can be used in meta:desc elements"""
    if len(description) <= 150:
        return description

    return description[0:147] + "..."


def ld_make_identifier(uri: str):
    """Returns a json-ld object node for the given URI"""
    return {
        "@id": uri,
    }


def ld_wrap_graph(graph):
    """Wraps a graph with a json-ld context."""
    return {
        "@context": [
            "https://www.w3.org/ns/anno.jsonld",
            {"@language": "sv"},
        ],
        "@graph": graph,
    }


def tag_parser(tags: str) -> list:
    """Custom tag parser for FornPunkt to ensure lower case tags."""
    return _parse_tags(tags.lower())


def fix_raa_record_description(description: str) -> str:
    """Fixes the description of a RAÄ/KMR record"""
    raa_description_suffix = "Beskrivningen är inte kvalitetssäkrad. Information kan saknas, vara felaktig eller inaktuell. Se även Inventeringsbok."
    description = description.replace(raa_description_suffix, "")

    if description == "":
        description = "Beskrivningen saknas eller är inte digitaliserad."

    return description


def fetch_raa_lamning(uuid):
    """Fetches a RAA lamning. Returns false if the lamning does not exist. Raises an error if RAA services can't be accessed."""

    if not is_possible_raa_id(uuid):
        return False

    try:
        r = requests.get(f"https://app.raa.se/open/fornsok/api/lamning/lamning/{uuid}")
        raa_data = r.json()
    except requests.exceptions.RequestException as e:
        raise Exception("RAA services are not available.") from e

    if r.status_code == 404:
        return False

    try:
        raa_data["beskrivning"] = fix_raa_record_description(raa_data["beskrivning"])
    except KeyError as e:
        sentry.capture_exception(e)
        raise Exception("Failed to find mandatory key.") from e

    item = dict()
    item["object"] = raa_data
    item["geojson"] = json.dumps(raa_data["nuvarande_lage"]["geometri"])
    item["description"] = create_meta_description(raa_data["beskrivning"])
    item["author"] = raa_data["publicerad_av_organisation"]
    item["uuid"] = raa_data["lamning_id"]

    # some lamnings have no geographic authorities as they are outside of Sweden (b65fe084-53f3-4ae4-8234-e1efb598e522)
    item["title"] = f"""{raa_data['lamningstyp_namn']} ({raa_data['lamningsnummer']})"""
    if len(raa_data["nuvarande_lage"]["geografisk_indelning"]["socken"]):
        item["title"] = (
            f"""{item['title']} {raa_data['nuvarande_lage']['geografisk_indelning']['socken'][0]['socken_namn']} socken, {raa_data['nuvarande_lage']['geografisk_indelning']['landskap'][0]['landskap_namn']}"""
        )

    return item


class UpstreamTimeoutExeption(Exception):
    pass


def fetch_raa_lamning_for_view(uuid):
    """Fetches and RAÄ lamning while returning errors for use from a view."""
    try:
        lamning = fetch_raa_lamning(uuid)
    except Exception as e:
        raise UpstreamTimeoutExeption()

    if not lamning:
        raise Http404("Lamningen finns inte.")

    return lamning


def get_soch_search_result(query, offset=0, limit=100):
    """Get search results from SOCH."""
    url = "https://www.kulturarvsdata.se/ksamsok/api"
    params = {
        "method": "search",
        "query": query,
        "recordSchema": "presentation",
        "startRecord": offset,
        "hitsPerPage": limit,
    }
    headers = {
        "Accept": "application/json",
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()
    except JSONDecodeError as e:
        raise Exception("RAA services are not available.") from e

    if response.status_code != 200:
        raise Exception("RAA services are not available.")

    formatted_data = {}
    formatted_data["total"] = data["result"]["totalHits"]
    formatted_data["results"] = []
    for result in data["result"]["records"]["record"]:
        formatted_data["results"].append(
            {
                "id": result["pres:item"]["pres:id"],
                # if the description only consists of a number it will be converted to a number by the parser
                # so we force it to be a string
                "description": fix_raa_record_description(str(result["pres:item"]["pres:description"])),
                "type": result["pres:item"]["pres:itemLabel"],
                "label": result["pres:item"]["pres:idLabel"],
            }
        )

    return formatted_data


observation_types_defination = {
    "@context": {
        "@language": "sv",
        "@vocab": "http://www.w3.org/2000/01/rdf-schema#",
        "schema": "http://schema.org/",
    },
    "@graph": [
        {
            "@type": "Class",
            "@id": "https://fornpunkt.se/observationstyper#fjarr",
            "label": "Fjärrobservation",
            "comment": "Observation gjord på distans utan ett besök i fält.",
            "schema:sameAs": ld_make_identifier("http://purl.org/heritagedata/schemes/agl_et/concepts/145156"),
            "subClassOf": ld_make_identifier("schema:Event"),
        },
        {
            "@type": "Class",
            "@id": "https://fornpunkt.se/observationstyper#falt",
            "label": "Fältobservation",
            "comment": "Observation gjord genom ett eller flera besök i fält.",
            "schema:sameAs": ld_make_identifier("http://purl.org/heritagedata/schemes/agl_et/concepts/147317"),
            "subClassOf": ld_make_identifier("schema:Event"),
        },
        {
            "@type": "Class",
            "@id": "https://fornpunkt.se/observationstyper#maskin",
            "label": "Maskinobservation",
            "comment": "Observation gjord av ett datorprogram genom dataanalys.",
            "subClassOf": ld_make_identifier("schema:Event"),
        },
    ],
}
