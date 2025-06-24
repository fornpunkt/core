import json
import secrets

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager
from taggit.models import GenericTaggedItemBase, TagBase

from .utilities import (
    centroid_from_feature,
    convert_geojson_to_schema_org,
    h_decode,
    h_encode,
    ld_make_identifier,
    sanitize_geojson_object,
    # validate_geojson, # No longer used as a field validator here
    validate_observation_type,
)
from django.core.exceptions import ValidationError # For save method
import geojson # For parsing in Lamning.save()


class Feedback(models.Model):
    """A model to hold feedback from users, this models does not have dependencies"""

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    message = models.TextField()
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message


class UserDetails(models.Model):
    """A model which holds extra information about a user"""

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    profile_privacy = models.CharField(
        max_length=2,
        choices=[
            ("PU", "Alla"),
            ("ME", "Inloggade FornPunkt användare"),
            ("PR", "Bara du"),
        ],
        default="PR",
    )

    user_description = models.TextField(blank=True)

    def get_absolute_url(self):
        return reverse("profile", args=self.user.username)


def create_user_details(sender, instance, created, **kwargs):
    """Create a UserDetails object for each new User"""
    if created:
        UserDetails.objects.create(user=instance)


models.signals.post_save.connect(create_user_details, sender=User)


class CustomTag(TagBase):
    """Custom Taggit Tag model"""

    created_time = models.DateTimeField(auto_now_add=True)
    changed_time = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True)
    wikipedia = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")

    @property
    def json_ld(self):
        """Return a JSON-LD representation of the tag"""
        graph = {
            "@type": "schema:DefinedTerm",
            "@id": "https://fornpunkt.se" + reverse(viewname="tag", args=(self.slug,)),
            "schema:name": self.name,
            "schema:url": ld_make_identifier("https://fornpunkt.se" + reverse(viewname="tag", args=(self.slug,))),
        }

        if self.wikipedia:
            graph["schema:subjectOf"] = ld_make_identifier(self.wikipedia)

        if self.description:
            graph["schema:description"] = self.description

        return graph


class TaggedThing(GenericTaggedItemBase):
    """Custom Taggit through model"""

    # GenericTaggedItemBase allows using the same tag for different kinds of objects

    tag = models.ForeignKey(
        CustomTag,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_items",
    )


class Lamning(models.Model):
    """Holds information about a lamning"""

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    title = models.TextField(max_length=150)
    tags = TaggableManager(blank=True, through=TaggedThing)

    geojson = models.TextField() # Removed validate_geojson validator
    center_lat = models.FloatField()
    center_lon = models.FloatField()

    created_time = models.DateTimeField(auto_now_add=True)
    changed_time = models.DateTimeField(auto_now=True)

    observation_type = models.CharField(
        max_length=2,
        choices=[("FO", "Fältobservation"), ("RO", "Fjärrobservation"), ("MO", "Maskinobservation")],
        blank=True,
        validators=[validate_observation_type],
    )

    hidden = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_time"]

    def save(self, *args, **kwargs):
        if not self.geojson:
            # This case should ideally be caught by model validation if field is not blank.
            # Raising ValidationError here ensures save() fails if geojson is empty/None.
            raise ValidationError({'geojson': _("GeoJSON content is required.")})

        parsed_geojson_obj = None
        try:
            # Use geojson.loads for initial parsing and structural validation
            parsed_geojson_obj = geojson.loads(self.geojson)
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            # Catches errors from json.loads if it's not valid JSON,
            # or ValueError from geojson library if structure is bad (e.g. invalid coordinate types)
            raise ValidationError({'geojson': _(f"Invalid GeoJSON string: {str(e)}")}) from e

        # The geojson library returns its own classes, not raw dicts directly for top level,
        # but they are dict-like. sanitize_geojson_object expects a dict.
        # We can convert it to a dict, or rely on its dict-like nature if sanitize_geojson_object handles it.
        # For safety, let's ensure it's a plain dict if sanitize_geojson_object strictly expects one.
        # However, geojson objects are often instances of geojson.feature.Feature etc.
        # which are dict-like. Let's assume sanitize_geojson_object can handle these dict-like objects.
        # The `is_valid` check is crucial.
        if not hasattr(parsed_geojson_obj, 'is_valid') or not parsed_geojson_obj.is_valid:
             raise ValidationError({'geojson': _("Invalid GeoJSON structure provided.")})

        try:
            # Pass the parsed object (which is dict-like) to sanitize_geojson_object
            # sanitize_geojson_object will perform our specific business rule validations
            # (e.g., must be Feature, specific geometry types, empty properties)
            sanitized_geojson_dict = sanitize_geojson_object(parsed_geojson_obj) # type: ignore
            self.geojson = json.dumps(sanitized_geojson_dict)
        except ValidationError as e: # Catch ValidationError from our sanitize_geojson_object
            # Propagate the validation error
            raise ValidationError({'geojson': e.messages}) from e

        # Calculate centroid from the newly sanitized GeoJSON string
        # centroid_from_feature also uses geojson.loads(), which is a bit redundant
        # but okay for now. It might fail if sanitized_geojson is not a Feature
        # or has no coordinates, which sanitize_geojson_object should prevent.
        try:
            center = centroid_from_feature(self.geojson)
            self.center_lat = center[1]
            self.center_lon = center[0]
        except Exception as e:
            # Handle cases where centroid calculation might fail even after sanitization
            # (e.g., if sanitize_geojson_object allowed an empty coordinate array that centroid_from_feature can't handle)
            # This indicates a potential issue or an edge case not fully covered.
            # For now, let's make sure lat/lon are not set or raise an error.
            # Given the strictness of sanitize_geojson_object, this should be rare.
            # Consider logging this error.
            raise ValidationError({'geojson': _(f"Could not calculate centroid from sanitized GeoJSON: {str(e)}")}) from e


        super(Lamning, self).save(*args, **kwargs)

    @property
    def hashid(self):
        return h_encode(self.id)

    @staticmethod
    def resolve_hashid(hash_identifier):
        return h_decode(hash_identifier)

    def get_absolute_url(self):
        return reverse("lamning", args=[self.id])

    @property
    def verbose_geojson(self):
        geojson = json.loads(self.geojson)
        geojson["properties"] = dict()
        geojson["properties"]["title"] = self.title
        geojson["properties"]["description"] = self.description
        geojson["properties"]["lamning_id"] = self.hashid
        geojson["properties"]["creator"] = self.user.username
        geojson["properties"]["tags"] = [tag.name for tag in self.tags.all()]
        geojson["properties"]["uri"] = f"https://fornpunkt.se{self.get_absolute_url()}"
        geojson["properties"]["observation_type"] = "falt" if self.observation_type == "FO" else "fjarr"

        return geojson

    @property
    def json_ld(self):
        graph = {
            "@type": "schema:CreativeWork",
            "@id": f"https://fornpunkt.se{self.get_absolute_url()}",
            "schema:name": self.title,
            "schema:text": self.description,
            "schema:creator": self.user.username,
            "schema:identifier": "FP-" + self.hashid,
            "schema:url": ld_make_identifier(f"https://fornpunkt.se{self.get_absolute_url()}"),
            "schema:discussionUrl": ld_make_identifier(f"https://fornpunkt.se{self.get_absolute_url()}#kommentarer"),
            "schema:provider": ld_make_identifier("https://fornpunkt.se"),
        }

        if self.observation_type:
            observaton_type = "falt" if self.observation_type == "FO" else "fjarr"
            observation_type = f"https://fornpunkt.se/observationstyper#{observaton_type}"
            graph["schema:event"] = {
                "@type": observation_type,
            }

        tags = list()
        for tag in self.tags.slugs():
            tags.append(ld_make_identifier(f"https://fornpunkt.se/tagg/{tag}"))
        graph["schema:keywords"] = tags

        graph["schema:contentLocation"] = convert_geojson_to_schema_org(self.geojson)

        return graph

    def __str__(self):
        return f"{self.title} by {self.user} at {self.created_time}"


class LamningWikipediaLink(models.Model):
    """Holds a link between a KMR lamning and a Wikipedia article"""

    kmr_lamning = models.UUIDField()
    wikipedia = models.URLField()
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.wikipedia.replace("https://sv.wikipedia.org/wiki/", "")

    @property
    def hashid(self):
        return h_encode(self.id)

    @property
    def json_ld(self):
        graph = {
            "@type": "Annotation",
            # NOTE: the w in the hashid, this is to avoid collisions with other annotation identifiers
            "@id": f"https://fornpunkt.se/raa/lamning/{self.kmr_lamning}#annoteringar-w_{self.hashid}",
            "generator": ld_make_identifier("https://fornpunkt.se"),
            "created": self.created_time.isoformat(sep="T", timespec="minutes") + "Z",
            "motivation": "linking",
            "body": {
                "schema:subjectOf": {
                    "@id": self.wikipedia,
                },
            },
            "target": {
                "@id": f"http://kulturarvsdata.se/raa/lamning/{self.kmr_lamning}",
            },
        }

        return graph


class KMRLamningType(models.Model):
    """Holds a KMR lamning type"""

    name = models.TextField()
    raa_id = models.IntegerField()
    description = models.TextField()
    slug = models.SlugField(max_length=75)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Comment(models.Model):
    """Generic comment model that is used for both FP sites and KMR ones"""

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()

    # comments can go on both FornPunkt lamningar and KMR ones
    lamning = models.ForeignKey(Lamning, on_delete=models.CASCADE, null=True, blank=True)
    raa_lamning = models.TextField(blank=True)  # RAÄ KMR UUID

    created_time = models.DateTimeField(auto_now_add=True)

    hidden = models.BooleanField(default=False)

    comment_type = models.CharField(max_length=2, choices=[("SR", "Skaderapport")], blank=True)

    class Meta:
        ordering = ["-created_time"]

    def __str__(self):
        return f"Kommentar av {self.user} vid {self.created_time}"

    @property
    def hashid(self):
        return h_encode(self.id)

    @property
    def json_ld(self):
        graph = {
            "@type": "Annotation",
            "generator": ld_make_identifier("https://fornpunkt.se"),
            "created": self.created_time.isoformat(sep="T", timespec="minutes") + "Z",
            "motivation": "commenting",
            "creator": {
                "@type": "foaf:Agent",
                "name": self.user.username,
            },
            "bodyValue": self.content,
        }

        if self.lamning:
            graph["@id"] = f"https://fornpunkt.se{self.lamning.get_absolute_url()}#kommentarer-{self.hashid}"
            graph["target"] = ld_make_identifier(f"https://fornpunkt.se{self.lamning.get_absolute_url()}")
        else:
            graph["@id"] = f"https://fornpunkt.se/raa/lamning/{self.raa_lamning}#kommentarer-{self.hashid}"
            graph["target"] = ld_make_identifier(f"http://kulturarvsdata.se/raa/lamning/{self.raa_lamning}")

        return graph


class Annotation(models.Model):
    """Generic annotation for litterature/references"""

    subject = models.UUIDField()
    target = models.URLField()
    created_time = models.DateTimeField(auto_now_add=True)
    changed_time = models.DateTimeField(auto_now=True)

    title = models.TextField()
    publisher = models.TextField()
    author_name_string = models.TextField(blank=True)
    target_type = models.TextField(blank=True)

    @property
    def hashid(self):
        return h_encode(self.id)

    def __str__(self):
        return f"<{ self.subject }> <{ self.target }>"

    @property
    def json_ld(self):
        graph = {
            "@type": "Annotation",
            "@id": f"https://fornpunkt.se/raa/lamning/{self.subject}#annoteringar-{self.hashid}",
            "generator": ld_make_identifier("https://fornpunkt.se"),
            "created": self.created_time.isoformat(sep="T", timespec="minutes") + "Z",
            "motivation": "linking",
            "body": {
                "schema:subjectOf": {
                    "@id": self.target,
                },
            },
            "target": {
                "@id": f"http://kulturarvsdata.se/raa/lamning/{self.subject}",
            },
        }

        return graph


class AccessToken(models.Model):
    """Holds a token that can be used to access the API"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rights = models.CharField(
        max_length=1,
        choices=(
            ("r", "Läs"),
            ("w", "Skriv"),
        ),
        default="r",
    )
    token = models.CharField(max_length=64, unique=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_hex(32)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} ({self.rights})"
