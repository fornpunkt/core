import csv
import json
import re
from itertools import chain
from operator import attrgetter

import requests
import sentry_sdk
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import (Http404, HttpResponse, HttpResponseBadRequest,
                         HttpResponseForbidden, HttpResponseRedirect,
                         JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.middleware.csrf import get_token, CsrfViewMiddleware
from django.urls import reverse, reverse_lazy
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.safestring import mark_safe
from django.views import generic
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from geojson import FeatureCollection
from taggit.utils import edit_string_for_tags

from .forms import LoginForm, SignUpForm
from .models import (AccessToken, Annotation, Comment, CustomTag, Feedback,
                     KMRLamningType, Lamning, LamningWikipediaLink,
                     TaggedThing, UserDetails)
from .utilities import (JsonApiResponse, UpstreamTimeoutExeption,
                        create_meta_description, fetch_raa_lamning_for_view,
                        get_soch_search_result, is_possible_raa_id, is_raa_id,
                        ld_wrap_graph, observation_types_defination,
                        replace_url_parameter, tag_parser)


def get_access_token_from_request(request):
    """Checks if the request has a valid access token."""
    access_token = request.headers.get("Authorization", None)
    if access_token:
        access_token = access_token.replace("Token ", "")
        try:
            access_token = AccessToken.objects.get(token=access_token)
            return access_token
        except AccessToken.DoesNotExist:
            return False
    return False


class LandingView(generic.TemplateView):
    """FornPunkt's main landing page"""

    template_name = "core/landing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["description"] = (
            "FornPunkt är en medborgarforskningsplattform med avsikten att göra det möjligt för vem som helst att bidra till insamling av information om platser i kulturlandskapet."
        )
        return context


class FeedbackCreateView(LoginRequiredMixin, SuccessMessageMixin, generic.edit.CreateView):
    """Feedback form"""

    template_name = "core/feedback_create.html"
    model = Feedback
    fields = ["message"]
    success_url = reverse_lazy("dashboard")
    success_message = "Din feedback har skickats. Tack!"

    def form_valid(self, form):
        form.instance.user = self.request.user

        return super(FeedbackCreateView, self).form_valid(form)


class LamningListView(LoginRequiredMixin, generic.list.ListView):
    """Lists lamnings per users"""

    model = Lamning
    template_name = "core/lamnings/list_lamningar.html"
    paginate_by = 10
    page_kwarg = "sida"
    lamning_filter = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["filter_string"] = ",".join(self.lamning_filter)
        current_page = context["page_obj"].number
        context["canonical"] = f"/lamningar?sida={current_page}"
        if self.lamning_filter:
            context["canonical"] += f'&filter={context["filter_string"]}'

        context["canonical"] = mark_safe(context["canonical"])
        return context

    def get_queryset(self):
        allowed_filters = ["saknar_taggar", "saknar_observationstyp"]
        self.lamning_filter = self.request.GET.get("filter", "").split(",")
        self.lamning_filter = [f for f in self.lamning_filter if f in allowed_filters]

        queryset = Lamning.objects.filter(user=self.request.user)
        if "saknar_taggar" in self.lamning_filter:
            queryset = queryset.filter(tags__isnull=True)
        if "saknar_observationstyp" in self.lamning_filter:
            queryset = queryset.filter(observation_type="")
        return queryset


class DashboardView(LoginRequiredMixin, generic.TemplateView):
    """User dashboard"""

    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recent_lamnings"] = Lamning.objects.all().filter(user=self.request.user)[:10]
        context["comments"] = Comment.objects.filter(
            lamning__in=Lamning.objects.all().filter(user=self.request.user)
        ).filter(hidden=False)
        return context


@method_decorator(xframe_options_exempt, name="dispatch")
class LamningEmbedView(generic.DetailView):
    """Lamning embed view - deprecated"""

    model = Lamning
    template_name = "core/lamnings/lamning_embed.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["description"] = create_meta_description(self.object.description)
        context["author"] = self.object.user
        context["title"] = self.object.title
        context["tags"] = self.object.tags.all()
        return context


class LamningView(generic.DetailView):
    """View for lamning registered in FornPunkt"""

    model = Lamning
    template_name = "core/lamnings/lamning.html"

    def get_context_data(self, **kwargs):
        if self.object.hidden and self.object.user != self.request.user:
            raise Http404

        context = super().get_context_data(**kwargs)
        context["description"] = create_meta_description(self.object.description)
        context["lat"] = str(self.object.center_lat).replace(",", ".")
        context["lon"] = str(self.object.center_lon).replace(",", ".")
        context["author"] = self.object.user
        context["title"] = self.object.title
        context["is_article"] = True
        context["comments"] = (
            Comment.objects.filter(hidden=False).filter(lamning=self.object.id).order_by("created_time")
        )  # TODO: apply filter
        context["tags"] = self.object.tags.all()
        return context


def lamning_jsonld(request, pk):
    """JSON-LD representation of a lamning"""
    lamning = get_object_or_404(Lamning, id=pk)
    graph = list([lamning.json_ld])

    comments = Comment.objects.filter(hidden=False).filter(lamning=lamning)
    for comment in comments:
        graph.append(comment.json_ld)

    return JsonApiResponse(ld_wrap_graph(graph), content_type="application/ld+json")


def lamning_geojson(request, pk):
    """GeoJSON representation of a lamning"""
    lamning = get_object_or_404(Lamning, id=pk)

    return JsonApiResponse(lamning.verbose_geojson, content_type="application/geo+json")


class CreateLamning(LoginRequiredMixin, generic.edit.CreateView):
    """Create lamning form"""

    template_name = "core/lamnings/lamning_create.html"
    model = Lamning
    fields = ["title", "tags", "description", "observation_type", "geojson"]

    def form_valid(self, form):
        form.instance.user = self.request.user

        if "_addanother" in self.request.POST:
            self.success_url = reverse("create_lamning") + "?continued=true"

        return super(CreateLamning, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class MultiCreateLamning(LoginRequiredMixin, generic.TemplateView):
    """Create multiple lamnings using the API"""

    template_name = "core/lamnings/lamning_create_multiple.html"

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name="testare").exists()


class UpdateLamning(LoginRequiredMixin, generic.edit.UpdateView):
    """Update lamning form"""

    template_name = "core/lamnings/lamning_edit.html"
    model = Lamning
    fields = ["title", "tags", "description", "observation_type", "geojson"]

    def get_object(self, queryset=None):
        lamning = generic.edit.UpdateView.get_object(self, queryset=None)
        if not lamning.user == self.request.user:
            raise Http404
        return lamning

    # TODO: does these form_valid() has an actual effect pr does the above run on POSTs?
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super(UpdateLamning, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tags_edit_string"] = edit_string_for_tags(self.object.tags.all())
        return context


class DeleteLamning(LoginRequiredMixin, generic.edit.DeleteView):
    """Delete lamning form"""

    template_name = "core/lamnings/lamning_delete.html"
    model = Lamning
    success_url = reverse_lazy("dashboard")

    def get_object(self, queryset=None):
        lamning = generic.edit.DeleteView.get_object(self, queryset=None)
        if not lamning.user == self.request.user:
            raise Http404
        return lamning


class MapView(generic.TemplateView):
    """Static map view other than metadata"""

    template_name = "core/karta.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["description"] = "Utforska FornPunkt och Kulturmiljöregistret ifrån FornPunkts karta."
        context["no_footer"] = True
        return context


class ExportView(LoginRequiredMixin, generic.TemplateView):
    """Static export view"""

    template_name = "core/export.html"


class UserView(generic.DetailView):
    """Profile view"""

    template_name = "core/profile.html"
    model = User
    slug_field = "username"
    context_object_name = "profile_user"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_details"] = UserDetails.objects.get(user=self.object)

        should_show_profile = False
        if context["user_details"].profile_privacy == "PU":
            should_show_profile = True
        elif context["user_details"].profile_privacy == "ME" and self.request.user.is_authenticated:
            should_show_profile = True

        if not self.object.is_active:
            should_show_profile = False
        elif self.object == self.request.user:
            should_show_profile = True

        if not should_show_profile:
            raise PermissionDenied()

        context["number_of_observations"] = Lamning.objects.filter(user=self.object).count()
        context["number_of_comments"] = Comment.objects.filter(user=self.object).count()

        if context["number_of_observations"] > 0:
            context["tag_cloud_data"] = (
                CustomTag.objects.filter(lamning__user=self.object)
                .annotate(num_lamnings=Count("lamning"))
                .order_by("-num_lamnings")
            )

            context["observation_type_count"] = (
                Lamning.objects.filter(user=self.object).values("observation_type").annotate(Count("observation_type"))
            )
            context["observation_type_count"] = {
                x["observation_type"]: x["observation_type__count"] for x in context["observation_type_count"]
            }

            context["observation_type_count"]["degrees"] = {}
            context["observation_type_count"]["degrees"][""] = str(
                360 / context["number_of_observations"] * context["observation_type_count"][""]
            ).replace(",", ".")
            context["observation_type_count"]["degrees"]["RO"] = str(
                360 / context["number_of_observations"] * context["observation_type_count"]["RO"]
            ).replace(",", ".")
            context["observation_type_count"]["degrees"]["FO"] = str(
                360 / context["number_of_observations"] * context["observation_type_count"]["FO"]
            ).replace(",", ".")

        # #TODO: can we query for the 20 latest lamnings and comments in one query?
        comments = Comment.objects.filter(user=self.object).order_by("-created_time")[:20]
        lamnings = Lamning.objects.filter(user=self.object).order_by("-created_time")[:20]
        context["activities"] = sorted(chain(comments, lamnings), key=attrgetter("created_time"), reverse=True)[:20]

        recent_lamnings = Lamning.objects.filter(user=self.object).order_by("-created_time")[:50]
        context["has_geojson"] = bool(recent_lamnings)
        context["geojson"] = FeatureCollection([lamning.verbose_geojson for lamning in recent_lamnings])

        context["profile_user"] = self.object

        return context


class SettingsView(LoginRequiredMixin, generic.TemplateView):
    """Static settings view"""

    template_name = "core/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["access_tokens"] = AccessToken.objects.filter(user=self.request.user)
        context["user"] = self.request.user
        context["user_details"] = UserDetails.objects.get(user=self.request.user)
        return context

    # form submission for display name
    def post(self, request, *args, **kwargs):
        if "display_name_submit" in request.POST:
            if "display_name" in request.POST:
                request.user.first_name = request.POST["display_name"]
                request.user.save()
            return redirect("settings")

        if "profile_privacy_submit" in request.POST:
            if "profile_privacy" in request.POST:
                user_details = UserDetails.objects.get(user=request.user)
                user_details.profile_privacy = request.POST["profile_privacy"]
                user_details.save()
            return redirect("settings")

        if "user_description_submit" in request.POST:
            if "user_description" in request.POST:
                user_details = UserDetails.objects.get(user=request.user)
                description = request.POST["user_description"]
                if len(description) > 200:
                    description = description[:200]
                user_details.user_description = description
                user_details.save()
            return redirect("settings")


def bbox(request):
    """Bounding box GeoJSON API"""

    # check if user-agent header is set
    if not request.META.get("HTTP_USER_AGENT"):
        return JsonApiResponse(
            {"error": "User-Agent saknas."},
            status=400,
        )

    # check if south, west, north, east are set #TODO we actually have this check below (MultiValueDictKeyError)
    if not all(k in request.GET for k in ("south", "west", "north", "east")):
        return JsonApiResponse(
            {"error": "Minst en parameter saknas."},
            status=400,
        )

    # TODO: can this be moved to after the queryset to save a check? or would the queryset be evaluated?
    # block users from trying to export all of fornpunkt.se using the map API
    try:
        if abs(float(request.GET["south"]) - float(request.GET["north"])) > 2:
            return JsonApiResponse(
                {"error": "Felaktig förfrågan."},
                status=400,
            )
    except ValueError:
        return JsonApiResponse(
            {"error": "Minst en parameter har ett felaktigt värde."},
            status=400,
        )

    try:
        queryset = Lamning.objects.filter(hidden=False).filter(
            Q(center_lon__lte=request.GET["east"])
            & Q(center_lon__gte=request.GET["west"])
            & Q(center_lat__gte=request.GET["south"])
            & Q(center_lat__lte=request.GET["north"])
        ).select_related("user").prefetch_related("tags")
    except MultiValueDictKeyError:
        return JsonApiResponse({"error": "Minst en parameter saknas."}, status=400)
    except ValueError:
        return JsonApiResponse({"error": "Minst en parameter har ett felaktigt värde."}, status=400)

    lamnings_geojson = [lamning.verbose_geojson for lamning in queryset]
    feature_collection = FeatureCollection(lamnings_geojson)

    return JsonApiResponse(feature_collection, content_type="application/geo+json")


def api_lamnings_export(request):
    """Method for exporting all lamnings of a user to various formats."""
    requested_format = request.GET.get("format", None)
    scope = request.GET.get("scope", None)

    access_token = get_access_token_from_request(request)
    if access_token:
        request.user = access_token.user

    if request.user.is_anonymous:
        return HttpResponseForbidden("Du måste vara inloggad för att exportera lamningar.")

    if scope == "all" and request.user.is_superuser:
        lamnings = Lamning.objects.filter(hidden=False)
    else:
        # an user can export their own lamnings even if they are hidden
        lamnings = Lamning.objects.filter(user=request.user)

    if requested_format == "tsv":
        response = HttpResponse(content_type="text/tsv")
        writer = csv.writer(response, delimiter="\t")
        writer.writerow(["id", "titel", "beskrivning", "geojson", "taggar", "användare", "skapad", "ändrad"])
        for lamning in lamnings:
            writer.writerow(
                [
                    lamning.hashid,
                    lamning.title,
                    lamning.description,
                    lamning.geojson,
                    "|".join([tag.name for tag in lamning.tags.all()]),
                    lamning.user,
                    lamning.created_time,
                    lamning.changed_time,
                ]
            )
        return response
    elif requested_format == "geojson":
        lamnings_geojson = [lamning.verbose_geojson for lamning in lamnings]
        feature_collection = FeatureCollection(lamnings_geojson)
        return JsonApiResponse(feature_collection, content_type="application/geo+json")
    else:
        lamnings_jsonld = [lamning.json_ld for lamning in lamnings]
        return JsonApiResponse(ld_wrap_graph(lamnings_jsonld), content_type="application/ld+json")


def api_tags_export(request):
    """Method for exporting all tags to json-ld."""
    access_token = get_access_token_from_request(request)
    if access_token:
        request.user = access_token.user

    if not request.user.is_superuser:
        return HttpResponseForbidden("Du måste vara inloggad som admin för att exportera taggar.")

    tags = CustomTag.objects.all()

    graph = list()
    for tag in tags:
        graph.append(tag.json_ld)

    return JsonApiResponse(ld_wrap_graph(graph), content_type="application/ld+json")


def api_comments_export(request):
    """Method for exporting all comments to json-ld."""
    scope = request.GET.get("scope", None)

    access_token = get_access_token_from_request(request)
    if access_token:
        request.user = access_token.user

    if scope == "all" and request.user.is_superuser:
        comments = Comment.objects.filter(hidden=False)
    else:
        comments = Comment.objects.filter(user=request.user)

    graph = list()
    for comment in comments:
        graph.append(comment.json_ld)

    return JsonApiResponse(ld_wrap_graph(graph), content_type="application/ld+json")


def api_accounts_export(request):
    """Method for exporting accounts to json-ld."""
    access_token = get_access_token_from_request(request)
    if access_token:
        request.user = access_token.user

    # no scopes are supported, you can only export your own account
    account = User.objects.filter(id=request.user.id)

    if not account.exists():
        return HttpResponseForbidden("Du måste vara inloggad för att exportera ditt konto.")

    graph = {
        "@type": "schema:Person",
        "@id": f"#{account[0].username}",
        "schema:alternateName": account[0].username,
        "schema:email": account[0].email,
    }

    if account[0].first_name:
        graph["schema:name"] = account[0].first_name

    return JsonApiResponse(ld_wrap_graph(graph), content_type="application/ld+json")


def api_lamning_wikipedia_link_export(request):
    """Method for exporting wikipedia links to json-ld."""
    access_token = get_access_token_from_request(request)
    if access_token:
        request.user = access_token.user

    if request.user.is_superuser:
        wikipedia_annotations = LamningWikipediaLink.objects.all()
    else:
        return HttpResponseForbidden("Du måste vara inloggad som admin för att exportera wikipedia-länkar.")

    graph = list()
    for annotation in wikipedia_annotations:
        graph.append(annotation.json_ld)

    return JsonApiResponse(ld_wrap_graph(graph), content_type="application/ld+json")


def api_lamning_annotation_link_export(request):
    """Method for exporting annotation links to json-ld."""
    access_token = get_access_token_from_request(request)
    if access_token:
        request.user = access_token.user

    if not request.user.is_superuser:
        return HttpResponseForbidden("Du måste vara inloggad som admin för att exportera anotationslänkar.")

    annotation_links = Annotation.objects.all()

    paginator = Paginator(annotation_links, per_page=1000)
    page_number = request.GET.get("page", 1)
    page = paginator.get_page(page_number)

    graph = [annotation.json_ld for annotation in page]
    response = JsonApiResponse(ld_wrap_graph(graph), content_type="application/ld+json")

    links = list()
    if page.has_next():
        links.append(
            f'<{replace_url_parameter(request.build_absolute_uri(), "page", page.next_page_number())}>; rel="next"'
        )
    if page.has_previous():
        links.append(
            f'<{replace_url_parameter(request.build_absolute_uri(), "page", page.previous_page_number())}>; rel="prev"'
        )
    links.append(f'<{replace_url_parameter(request.build_absolute_uri(), "page", paginator.num_pages)}>; rel="last"')

    response["Link"] = ", ".join(links)

    return response


@csrf_exempt
def api_lamning_annotation_link_create(request):
    """Method for creating annotation links."""
    access_token = get_access_token_from_request(request)
    if access_token:
        request.user = access_token.user

    if not access_token or not request.user.is_superuser or not access_token.rights == "w":
        return HttpResponseForbidden("Du måste vara inloggad för att skapa anotationslänkar.")

    # title, subject, target, type must be present, publisher and author_name_string are optional
    if (
        "title" not in request.POST
        or "subject" not in request.POST
        or "target_type" not in request.POST
        or "target" not in request.POST
    ):
        return HttpResponseBadRequest("Du måste ange titel, ämne, mål och typ.")

    allowed_types = ["Bok", "Artikel", "Databas", "Fältinsamling", "Rapport", "Uppdrag", "Video"]

    try:
        annotation = Annotation()
        annotation.title = request.POST["title"]
        annotation.subject = request.POST["subject"]
        annotation.target_type = request.POST["target_type"]
        annotation.target = request.POST["target"]
        if request.POST["target_type"] not in allowed_types:
            return HttpResponseBadRequest("Ogiltig typ.")
        if "publisher" in request.POST:
            annotation.publisher = request.POST["publisher"]
        if "author_name_string" in request.POST:
            annotation.author_name_string = request.POST["author_name_string"]
        annotation.save()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return HttpResponseBadRequest("Något gick fel.")

    response = JsonApiResponse(annotation.json_ld, content_type="application/ld+json")
    response.status_code = 201
    return response


@login_required
def create_comment(request, lamning):  # TODO split this into two endpoints
    """API-view which currently manages comments from both KMR sites and FP ones"""
    raa_lamning = False
    fornpunkt_lamning = False

    if is_possible_raa_id(lamning):
        raa_lamning = True
    else:
        lamning = get_object_or_404(Lamning, pk=Lamning.resolve_hashid(lamning))
        fornpunkt_lamning = True

    def error(message):
        messages.error(request, message)
        if fornpunkt_lamning:
            return redirect("/lamning/" + lamning.hashid)
        else:
            return redirect("/raa/lamning/" + lamning)

    try:
        comment = request.POST["comment"]
        if comment == "":
            return error("Något gick fel.")
    except Exception as e:  # TODO: do not use bare except
        sentry_sdk.capture_exception(e)
        return error("Något gick fel.")

    if fornpunkt_lamning:
        full_comment = Comment(user=request.user, content=comment, lamning=lamning)
        full_comment.save()
        return HttpResponseRedirect(reverse("lamning", args=(lamning.id,)))
    else:
        full_comment = Comment(user=request.user, content=comment, raa_lamning=lamning)
        full_comment.save()
        return HttpResponseRedirect(reverse("raa_lamning", args=(lamning,)))


@csrf_exempt
def api_lamning_create(request):
    """API-view for creating a lamning from a GeoJSON string."""

    # TODO: For all API views, allow only the intended HTTP methods

    access_token = get_access_token_from_request(request)
    if access_token:
        request.user = access_token.user

        if not access_token.rights == "w":
            return HttpResponseForbidden("Du måste ha skrivrättigheter för att skapa lämningar.")
    else:
        # if there is no access token, check if the user is logged in
        if request.user.is_anonymous:
            return HttpResponseForbidden("Du måste vara inloggad för att skapa lämningar.")

        csrf_middleware = CsrfViewMiddleware(lambda r: r)
        csrf_result = csrf_middleware.process_view(request, None, (), {})
        # if csrf_result is not None, the CSRF check failed
        if csrf_result is not None:
            return HttpResponseForbidden()

    json_data = json.loads(request.body)

    if not isinstance(json_data, dict) or "features" not in json_data or len(json_data["features"]) != 1:
        return HttpResponseBadRequest("GeoJSON objektet måste innehålla en feature.")

    properties = json_data["features"][0]["properties"]
    title = properties.get("title", None)
    description = properties.get("description", None)
    tags_string = properties.get("tags", None)
    observation_type = properties.get("observation_type", None)

    if not title:
        return HttpResponseBadRequest("Du måste ange en titel.")

    if not isinstance(title, str):
        return HttpResponseBadRequest("Titeln måste vara en sträng.")

    if not description:
        return HttpResponseBadRequest("Du måste ange en beskrivning.")

    if not isinstance(description, str):
        return HttpResponseBadRequest("Beskrivningen måste vara en sträng.")

    if not tags_string or not tags_string.strip():
        return HttpResponseBadRequest("Du måste ange en eller flera taggar.")

    if not isinstance(tags_string, str):
        return HttpResponseBadRequest("Taggarna måste vara en angivna som en komma-separerad sträng.")

    if not observation_type:
        return HttpResponseBadRequest('Du måste ange en observationstyp, antigen "FO", "MO" eller "RO".')

    if observation_type not in ["FO", "MO", "RO"]:
        return HttpResponseBadRequest('Ogiltig observationstyp. Tillåtna värden är "FO", "MO" eller "RO".')

    # remove properties from the geojson
    json_data["features"][0]["properties"] = {}
    geojson_data = json.dumps(json_data["features"][0])

    try:
        lamning = Lamning(
            user=request.user,
            geojson=geojson_data,
            title=title,
            description=description,
            observation_type=observation_type,
        )
        lamning.full_clean(exclude=["center_lat", "center_lon"])
        lamning.save()
        tags = tag_parser(tags_string)
        lamning.tags.add(*tags)
    except Exception as e: # TODO: do not use bare except
        sentry_sdk.capture_exception(e)
        return HttpResponseBadRequest("Något gick fel.")

    response = JsonApiResponse(lamning.geojson, content_type="application/geo+json")
    response.status_code = 201
    return response


class TagListView(generic.list.ListView):
    """View for listing all tags."""

    model = CustomTag
    template_name = "core/tags/list_tags.html"
    page_kwarg = "sida"
    paginate_by = 15
    context_object_name = "tags"
    tag_filter = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["filter_string"] = ",".join(self.tag_filter)
        current_page = context["page_obj"].number
        context["canonical"] = f"/taggar?sida={current_page}"
        if self.tag_filter:
            context["canonical"] = f'/taggar?sida={current_page}&filter={context["filter_string"]}'

        page_count = context["paginator"].num_pages
        context["description"] = f"Lista över alla taggar i FornPunkt. Sida {current_page} av {page_count}."

        context["canonical"] = mark_safe(context["canonical"])
        return context

    def get_queryset(self):
        allowed_filters = ["saknar_wikipedia", "saknar_beskrivning"]

        self.tag_filter = self.request.GET.get("filter", "").split(",")
        self.tag_filter = [f for f in self.tag_filter if f in allowed_filters]

        queryset = CustomTag.objects.all().order_by("name")
        if "saknar_wikipedia" in self.tag_filter:
            queryset = queryset.filter(wikipedia="")
        if "saknar_beskrivning" in self.tag_filter:
            queryset = queryset.filter(description="")
        return queryset


class TagView(generic.DetailView, generic.list.MultipleObjectMixin):
    """Tag view which also lists all sites for the tag."""

    template_name = "core/tags/tag.html"
    model = CustomTag
    paginate_by = 15
    page_kwarg = "sida"
    allow_empty = True

    def get_context_data(self, **kwargs):
        object_list = Lamning.objects.filter(hidden=False).filter(tags__slug=self.kwargs["slug"]).select_related("user")
        context = super(TagView, self).get_context_data(object_list=object_list, **kwargs)
        context["description"] = create_meta_description(self.object.description)
        context["title"] = self.object.name

        current_page = context["page_obj"].number
        if current_page > 1:
            context["canonical"] = f"/tagg/{self.object.slug}?sida={current_page}"
        return context


class TagUpdateView(UserPassesTestMixin, generic.edit.UpdateView):
    """Update view for tags only accessible to "redigerare" which only can edit the description."""

    template_name = "core/tags/tag_edit.html"
    model = CustomTag
    fields = ["description"]

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name="redigerare").exists()

    def get_success_url(self):
        return reverse("tag", kwargs={"slug": self.object.slug})


def tag_jsonld(request, slug):
    """JSON-LD representation of a tag"""
    tag = get_object_or_404(CustomTag, slug=slug)

    return JsonApiResponse(ld_wrap_graph(tag.json_ld), content_type="application/ld+json")


def raa_lamning(request, record_id):
    """View for displaying a single lamning from KMR."""
    try:
        lamning = fetch_raa_lamning_for_view(record_id)
    except Http404:
        response = HttpResponse()
        response.status_code = 404
        response.content = "Kunde inte hitta någon lämning ifrån Riksantikvarieämbetet med den identifieraren."
        return response
    except UpstreamTimeoutExeption:
        response = HttpResponse()
        response.status_code = 504
        response.content = "Kunde inte hämta infromation ifrån Riksantikvarieämbetet."
        return response

    context = {**lamning}
    context["comments"] = Comment.objects.filter(hidden=False).filter(raa_lamning=record_id).order_by("created_time")
    wikipedia = LamningWikipediaLink.objects.filter(kmr_lamning=record_id).first()
    annotations = Annotation.objects.filter(subject=record_id)

    if annotations:
        context["annotations"] = annotations
    if wikipedia:
        context["wikipedia"] = wikipedia.wikipedia

    context["is_article"] = True
    return render(request, "core/raa_lamning.html", context)


def raa_lamning_jsonld(request, record_id):
    """JSON-LD representation of a lamning from KMR(annotations only)"""
    comments = Comment.objects.filter(hidden=False).filter(raa_lamning=record_id)
    wikipedia_annotations = LamningWikipediaLink.objects.filter(kmr_lamning=record_id)
    annotations = Annotation.objects.filter(subject=record_id)

    graph = list()
    for comment in comments:
        graph.append(comment.json_ld)

    for wikipedia_annotation in wikipedia_annotations:
        graph.append(wikipedia_annotation.json_ld)

    for annotation in annotations:
        graph.append(annotation.json_ld)

    return JsonApiResponse(ld_wrap_graph(graph), content_type="application/ld+json")


def get_feature_info(request):
    """Proxy for getting feature info from the RAÄ."""
    # TODO: errors and such
    url = "https://karta.raa.se/geo/arkreg_v1.0/wms"
    r = requests.get(url, params=dict(request.GET))

    return JsonResponse(r.json(), safe=False)


class CustomLoginView(LoginView):
    """View for logging in."""

    form_class = LoginForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["description"] = (
            "Logga in på FornPunkt för att börja dela med dig av information om kultur- och fornlämningar."
        )
        context["canonical"] = "/auth/login"
        return context

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return super().get(request, *args, **kwargs)


def signup(request):
    """View for signing up."""

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()  # load the profile instance created by the signal
            user.is_active = False  # disable the user awaiting email confirmation
            user.save()
            email = form.cleaned_data.get("email")

            current_site = get_current_site(request)
            subject = "Bekräfta din e-postadress"
            message = render_to_string(
                "registration/account_activation_email.txt",
                {
                    "user": user,
                    "domain": current_site.domain,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user),
                },
            )
            user.email_user(subject, message)

            # redirect user to home page
            messages.success(
                request,
                f"Ett e-postmeddelande har skickats till {email}. Kontrollera din inkorg och bekräfta din e-postadress.",
            )
            return redirect("login")
        else:
            # form error
            return render(request, "registration/signup.html", {"form": form})

    form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})


def activate_account(request, uidb64, token):
    """View for activating a user."""
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect("dashboard")

    messages.success(request, "Konto kunde inte aktiveras. Kontrollera att du har kopierat rätt länk.")
    return redirect("login")


class ObservationTypesView(generic.TemplateView):
    """Page for listing all observation types."""

    template_name = "core/observationstyper.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["description"] = "Lista över alla observationstyper som kan användas vid en registrering i FornPunkt."
        context["is_article"] = True
        context["types"] = observation_types_defination["@graph"]

        # map ['@id'] to ['id'] so it can be used in the template
        for t in context["types"]:
            t["id"] = t["@id"]
        return context


def observationtypes_jsonld(request):
    """View for static observation types as JSON-LD."""
    graph = observation_types_defination

    return JsonApiResponse(graph, content_type="application/ld+json")


def l_number_redirection(request, l_number):
    """View for redirecting L-numbers to the correct page."""
    r = requests.post(
        "https://app.raa.se/open/fornsok/proxy/api/lamning/search/lamning",
        json={"criteria": {"lamningsnummer_eller_raa_nummer": [l_number]}},
    )

    response_data = r.json()

    try:
        if response_data["total_size"] != 1:
            raise Http404
        elif request.GET.get("target") == "kulturarvsdata":
            # NOTE: this is used by external apps and or reconcilliation services
            uuid = response_data["results"][0]["lamning_id"]
            return redirect(f"https://kulturarvsdata.se/raa/lamning/{uuid}")
        else:
            uuid = response_data["results"][0]["lamning_id"]
            return redirect(reverse(viewname="raa_lamning", kwargs={"record_id": uuid}))
    except KeyError as e:
        raise Http404 from e


def identification_resolver(request, identifier):
    """'View for resolving KMR identifiers to a specific record"""
    l_number_regex = re.compile(r"^L\d{4}:\d+$")

    if is_raa_id(identifier):
        result = identifier
    elif l_number_regex.match(identifier):
        r = requests.post(
            "https://app.raa.se/open/fornsok/proxy/api/lamning/search/lamning",
            json={"criteria": {"lamningsnummer_eller_raa_nummer": [identifier]}},
        )

        response_data = r.json()
        try:
            result = response_data["results"][0]["lamning_id"]
        except (KeyError, IndexError) as e:
            raise Http404 from e
    else:
        raise Http404

    if request.GET.get("target") == "kulturarvsdata":
        url = f"https://kulturarvsdata.se/raa/lamning/{result}"
    else:
        url = "https://fornpunkt.se" + reverse(viewname="raa_lamning", kwargs={"record_id": result})

    if request.GET.get("plaintext"):
        return HttpResponse(url, content_type="text/plain")
    return redirect(url)


class RaaTypeListView(generic.ListView):
    """List of RAA record types."""

    model = KMRLamningType
    template_name = "core/raa_type_list.html"
    page_kwarg = "sida"
    context_object_name = "types"
    paginate_by = 1000  # ensure all types are shown

    def get_context_data(self, **kwargs):
        context = super(RaaTypeListView, self).get_context_data(**kwargs)
        context["description"] = create_meta_description("Lämningstyper ifrån Riksantikvarieämbetet.")
        context["title"] = "Lämningstyper"

        return context


class RaaTypeView(generic.DetailView):
    """List of RAA records of a specific type."""

    model = KMRLamningType
    template_name = "core/raa_type.html"
    page = 1

    def get_context_data(self, **kwargs):
        # TODO catch upstream errors
        object_list = get_soch_search_result(
            f'itemClassName="{self.object.name}" AND serviceName="kmr_lamningar"', offset=(self.page - 1) * 100
        )
        total_size = object_list["total"]
        context = super(RaaTypeView, self).get_context_data(object_list=object_list["results"], **kwargs)
        context["description"] = create_meta_description(self.object.description)
        context["title"] = self.object.name

        total_number_of_pages = total_size // 100 + 1
        current_page = self.page
        context["paginator"] = {}
        context["page_obj"] = {}
        context["page_obj"]["paginator"] = {}
        context["page_obj"]["paginator"]["num_pages"] = total_number_of_pages
        context["page_obj"]["number"] = current_page
        context["paginator"]["count"] = total_number_of_pages
        if current_page > 1:
            context["canonical"] = f"/raa/typer/{self.object.slug}?sida={current_page}"
            context["page_obj"]["previous_page_number"] = current_page - 1
            context["page_obj"]["has_previous"] = True
        else:
            context["page_obj"]["previous_page_number"] = None
            context["page_obj"]["has_previous"] = False

        if current_page < total_number_of_pages:
            context["page_obj"]["next_page_number"] = current_page + 1
            context["page_obj"]["has_next"] = True
        return context

    def get_queryset(self):
        self.page = int(self.request.GET.get("sida", 1))

        return super(RaaTypeView, self).get_queryset()


def report_client_error_to_sentry(request):
    """View for reporting client errors to Sentry."""
    payload = json.loads(request.body)
    error = payload["error"]
    line = payload["line"]
    url = payload["url"]
    script = payload["script"]

    # TODO: capture javascript stacktrace
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("line", line)
        scope.set_tag("url", url)
        scope.set_tag("script", script)

        sentry_sdk.capture_message(error, "fatal")

    return HttpResponse(status=201)


def dataset_rdf_proxy(request):
    """Proxies Turtle RDF for our DCAT/VoID definations."""
    r = requests.get("https://fornpunkt.se/data/data.ttl")
    return HttpResponse(r.text, content_type="text/turtle")
