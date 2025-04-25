from django.contrib.sitemaps.views import sitemap
from django.urls import path, register_converter
from django.views.generic import RedirectView, TemplateView

from . import feeds, views
from .sitemaps import sitemaps
from .utilities import HashIdConverter

register_converter(HashIdConverter, 'hashid')

# TODO we could get rid of the inner_view functions
def logged_in_switch_view(logged_in_view, logged_out_view):
    '''Checks if the user is logged in and if so returns a logged in view othervise returns a logged out view'''

    def inner_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            return logged_in_view(request, *args, **kwargs)
        return logged_out_view(request, *args, **kwargs)

    return inner_view


def content_negotiation(content_formats, default_view):
    '''Returns a view that will return the correct view based on the accept header'''

    def negotiate(request, *args, **kwargs):
        # split media types, normalize, and finaly remove parameters
        requested_formats = request.headers.get('accept', '').lower().split(',')
        requested_formats = [f.split(';')[0].strip() for f in requested_formats]

        for requested_format in requested_formats:
            if requested_format in content_formats:
                return content_formats[requested_format](request, *args, **kwargs)

        return default_view(request, *args, **kwargs)

    return negotiate


lamning_negotiation_formats = {
    'text/html': views.LamningView.as_view(),
    'application/ld+json': views.lamning_jsonld,
    'application/geo+json': views.lamning_geojson,
    'application/rss+xml': feeds.LamningCommentFeed(),
    'application/json': views.lamning_jsonld,
}

raa_lamning_negotiation_formats = {
    'text/html': views.raa_lamning,
    'application/ld+json': views.raa_lamning_jsonld,
    'application/rss+xml': feeds.RaaLamningCommentFeed(),
    'application/json': views.raa_lamning_jsonld,
}

tag_negotiation_formats = {
    'text/html': views.TagView.as_view(),
    'application/ld+json': views.tag_jsonld,
    'application/rss+xml': feeds.TaggedLamningsFeed(),
    'application/json': views.tag_jsonld,
}

observation_types_negotiation_formats = {
    'text/html': views.ObservationTypesView.as_view(),
    'application/ld+json': views.observationtypes_jsonld,
    'application/json': views.observationtypes_jsonld,
}

urlpatterns = [
    # icons and manifests
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico')),
    path('favicon.svg', RedirectView.as_view(url='/static/favicon.svg')),
    path('android-chrome-192x192.png', RedirectView.as_view(url='/static/android-chrome-192x192.png')),
    path('android-chrome-512x512.png', RedirectView.as_view(url='/static/android-chrome-512x512.png')),
    path('apple-touch-icon.png', RedirectView.as_view(url='/static/apple-touch-icon.png')),
    path('safari-pinned-tab.svg', RedirectView.as_view(url='/static/safari-pinned-tab.svg')),
    path('manifest.json', TemplateView.as_view(template_name='core/manifest.json', content_type='application/json')),

    path('', logged_in_switch_view(views.DashboardView.as_view(), views.LandingView.as_view()), name='dashboard'),
    path('karta', views.MapView.as_view(), name='map'),
    path('exportera', views.ExportView.as_view(), name='export'),
    path('auth/signup', views.signup, name='signup'),
    path('auth/login', views.CustomLoginView.as_view(), name='login'),
    path('auth/activate/<str:uidb64>/<str:token>', views.activate_account, name='activate_account'),
    path('feedback', views.FeedbackCreateView.as_view(), name='feedback_create'),
    path('installningar', views.SettingsView.as_view(), name='settings'),
    path('fp-internal-sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('anvandare/<str:slug>', views.UserView.as_view(), name='profile'),
    path('anvandare/<str:slug>/lamningar.rss', feeds.UserLamningsFeed(), name='user_lamnings_rss'),

    path('observationstyper', content_negotiation(observation_types_negotiation_formats, views.ObservationTypesView.as_view()), name='observationtypes'),
    path('observationstyper.jsonld', views.observationtypes_jsonld, name='observationtypes_jsonld'),

    path('lamningar', views.LamningListView.as_view(), name='list_lamning'),
    path('lamning/skapa', views.CreateLamning.as_view(), name='create_lamning'),
    path('lamning/skapa-flera', views.MultiCreateLamning.as_view(), name='create_multiple_lamning'),
    path('lamning/<hashid:pk>/embed', views.LamningEmbedView.as_view(), name='lamning_embed'),
    path('lamning/<hashid:pk>.jsonld', views.lamning_jsonld, name='lamning_jsonld'),
    path('lamning/<hashid:pk>.geojson', views.lamning_geojson, name='lamning_geojson'),
    path('lamning/<hashid:pk>.rss', feeds.LamningCommentFeed(), name='lamning_comment_rss'),
    path('lamning/<hashid:pk>/redigera', views.UpdateLamning.as_view(), name='update_lamning'),
    path('lamning/<hashid:pk>/radera', views.DeleteLamning.as_view(), name='delete_lamning'),
    path('lamning/<hashid:pk>', content_negotiation(lamning_negotiation_formats, views.LamningView.as_view()) , name='lamning'),

    path('taggar', views.TagListView.as_view(), name='tag_list'),
    path('tagg/<str:slug>.rss', feeds.TaggedLamningsFeed(), name='tag_rss'),
    path('tagg/<str:slug>.jsonld', views.tag_jsonld, name='tag_jsonld'),
    path('tagg/<str:slug>', content_negotiation(tag_negotiation_formats, views.TagView.as_view()), name='tag'),
    path('tagg/<str:slug>/redigera', views.TagUpdateView.as_view(), name='tag_update'),

    path('api/lamnings/bbox', views.bbox, name='bbox'),
    path('api/create-comment/<lamning>', views.create_comment, name='create_comment'),
    path('api/annotation-links/create', views.api_lamning_annotation_link_create, name='api_annotation_links_create'), # NOTE: deprecated
    # l-number redirection API v1 deprecated
    path('api/l-number-redirection/<l_number>', views.l_number_redirection, name='l_number_redirection'),

    # l-number redirection API v2
    path('apis/kmr-identification-resolver/v1/<identifier>', views.identification_resolver, name='identification_resolver'),

    # NOTE: deprecated
    # export API v1
    path('api/annotation-links/export', views.api_lamning_annotation_link_export, name='api_annotation_links_export'),
    path('api/lamnings/export', views.api_lamnings_export, name='api_lamnings_export'),
    path('api/tags/export', views.api_tags_export, name='api_tags_export'),
    path('api/comments/export', views.api_comments_export, name='api_comments_export'),
    path('api/accounts/export', views.api_accounts_export, name='api_accounts_export'),
    path('api/wikipedia-links/export', views.api_lamning_wikipedia_link_export, name='api_wikipedia_links_export'),

    # export API v2
    path('apis/export/lamnings', views.api_lamnings_export, name='api_lamnings_export'),
    path('apis/export/tags', views.api_tags_export, name='api_tags_export'),
    path('apis/export/comments', views.api_comments_export, name='api_comments_export'),
    path('apis/export/accounts', views.api_accounts_export, name='api_accounts_export'),
    path('apis/export/wikipedia-annotations', views.api_lamning_wikipedia_link_export, name='api_wikipedia_links_export'),
    path('apis/export/generic-annotations', views.api_lamning_annotation_link_export, name='api_annotation_links_export'),

    # create API v1
    path('apis/create/v1/lamning', views.api_lamning_create, name='api_lamning_create'),
    path('apis/create/v1/annotation', views.api_lamning_annotation_link_create, name='api_annotation_create'),

    # skaderapporter API
    path('apis/skaderapporter/v1/rss', feeds.SkaderapporterFeed(), name='api_skaderapporter'),

    path('raa/lamning/<str:record_id>.jsonld', views.raa_lamning_jsonld, name='raa_lamning_jsonld'),
    path('raa/lamning/<str:record_id>.rss', feeds.RaaLamningCommentFeed(), name='raa_lamning_comment_rss'),
    path('raa/lamning/<str:record_id>', content_negotiation(raa_lamning_negotiation_formats, views.raa_lamning), name='raa_lamning'),

    path('raa/typer', views.RaaTypeListView.as_view(), name='raa_type_list'),
    path('raa/typer/<str:slug>', views.RaaTypeView.as_view(), name='raa_type'),

    path('raa/wms-proxy', views.get_feature_info, name='proxy'),

    path('datasets', views.dataset_rdf_proxy, name='datasets'),
    path('.well-known/void', RedirectView.as_view(permanent=False, pattern_name='datasets'), name='void'),

    path('robots.txt', TemplateView.as_view(template_name='core/robots.txt', content_type='text/plain')),

    path('.well-known/security.txt', TemplateView.as_view(template_name='core/security.txt', content_type='text/plain'), name='security_txt'),
    path('security.txt', RedirectView.as_view(permanent=False, pattern_name='security_txt')),

    path('report-client-error', views.report_client_error_to_sentry, name='report_client_error'),
]
