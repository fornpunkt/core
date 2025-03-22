import geojson
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils.feedgenerator import Rss201rev2Feed

from .models import Comment, CustomTag, Lamning, UserDetails
from .utilities import fetch_raa_lamning_for_view


class SimpleGeoRSSAtomFeed(Rss201rev2Feed):
    '''Feed for lamnings with a given tag'''

    def __init__(self, title, link, description, **kwargs):
        super().__init__(title, link, description, **kwargs)

    def root_attributes(self):
        attrs = super().root_attributes()
        attrs['xmlns:georss'] = 'http://www.georss.org/georss'
        return attrs

    def add_item_elements(self, handler, item):
        super().add_item_elements(handler, item)
        parsed_geojson = geojson.loads(item.get('geojson'))
        if parsed_geojson.geometry.type.lower() == 'point':
            handler.addQuickElement('georss:point', f'{parsed_geojson.geometry.coordinates[1]} {parsed_geojson.geometry.coordinates[0]}')
        elif parsed_geojson.geometry.type.lower() == 'linestring':
            handler.addQuickElement('georss:line', ' '.join(f'{c[1]} {c[0]}' for c in parsed_geojson.geometry.coordinates))
        elif parsed_geojson.geometry.type.lower() == 'polygon':
            handler.addQuickElement('georss:polygon', ' '.join(f'{c[1]} {c[0]}' for c in parsed_geojson.geometry.coordinates[0]))


class TaggedLamningsFeed(Feed):

    feed_type = SimpleGeoRSSAtomFeed

    '''Feed for lamnings with a given tag'''
    def get_object(self, request, slug):
        return CustomTag.objects.get(slug=slug)

    def title(self, item):
        return f'Lämningar taggade med {item.name}'

    def link(self, item):
        return reverse(viewname='tag', args=(item.slug,))

    def description(self, item):
        return f'Senaste lämningarna ifrån FornPunkt taggade med {item.name}.'

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.description

    def item_author_name(self, item):
        return item.user.username

    def item_link(self, item):
        return item.get_absolute_url()

    def item_extra_kwargs(self, item):
        extra_kwargs = super().item_extra_kwargs(item)
        extra_kwargs['geojson'] = item.geojson
        return extra_kwargs

    def items(self, obj):
        return Lamning.objects.filter(tags__slug=obj.slug).filter(hidden=False).order_by('-created_time').select_related(('user'))[:30]

class UserLamningsFeed(Feed):
    '''Feed for lamnings by a given user'''

    def get_object(self, request, slug):
        user = User.objects.get(username=slug)
        if not UserDetails.objects.get(user=user).profile_privacy == 'PU':
            raise PermissionDenied()
        return user

    feed_type = SimpleGeoRSSAtomFeed

    def title(self, item):
        return f'Lämningar av {item.username}'

    def link(self, item):
        return reverse(viewname='profile', args=(item.username,))

    def description(self, item):
        return f'Senaste lämningarna registrerade av användaren {item.username}.'

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.description

    def item_author_name(self, item):
        return item.user.username

    def item_link(self, item):
        return item.get_absolute_url()

    def item_extra_kwargs(self, item):
        extra_kwargs = super().item_extra_kwargs(item)
        extra_kwargs['geojson'] = item.geojson
        return extra_kwargs

    def items(self, obj):
        return Lamning.objects.filter(user=obj).filter(hidden=False).order_by('-created_time')[:30]


class LamningCommentFeed(Feed):
    '''Comment feed for a given FP lamning'''
    def get_object(self, request, pk):
        self.object = Lamning.objects.get(id=pk)
        return self.object

    def title(self, item):
        return f'Kommentarer till lämningen "{item.title}"'

    def link(self, item):
        return item.get_absolute_url() + '#kommentarer'

    def description(self, item):
        return f'De senaste kommentarerna till lämningen "{item.title}"'

    def item_title(self, item):
        return f'{item.user.username} kommenterade {self.object.title}'

    def item_description(self, item):
        return item.content

    def item_author_name(self, item):
        return item.user.username

    def item_link(self, item):
        return f'{self.object.get_absolute_url()}#kommentarer'

    def item_pubdate(self, item):
        return item.created_time

    def items(self, obj):
        return Comment.objects.filter(hidden=False).filter(lamning = obj.id).order_by('-created_time')[:30]


class RaaLamningCommentFeed(Feed):
    '''Comment feed for a given RAÄ lamning'''
    def get_object(self, request, record_id):
        self.lamning = fetch_raa_lamning_for_view(record_id)
        self.url = reverse(viewname='raa_lamning', args=(self.lamning['uuid'],)) + '#kommentarer'
        return self.lamning

    def title(self, item):
        return 'Kommentarer till lämningen "' + item['title'] + '"'

    def link(self, item):
        return self.url

    def description(self, item):
        return 'De senaste kommentarerna till lämningen "' + item['title'] + '"'

    def item_title(self, item):
        return f'{item.user.username} kommenterade ' + self.lamning['title']

    def item_description(self, item):
        return item.content

    def item_author_name(self, item):
        return item.user.username

    def item_link(self, item):
        return self.url

    def item_pubdate(self, item):
        return item.created_time

    def items(self, obj):
        return Comment.objects.filter(hidden=False).filter(raa_lamning = obj['uuid']).order_by('-created_time')[:30]


class SkaderapporterFeed(Feed):
    '''Lists all comments with comment_type set to SR'''

    language = 'sv'
    title = 'Skaderapporter'
    description = 'Kommentarer ifrån FornPunkts användare, klassifierade av FornPunkt som skaderapporter.'
    link = 'apis/skaderapporter/v1/rss' # TODO can we set this using reverse() somehow? (it's a circular import)

    def item_link(self, item):
        return reverse(viewname='raa_lamning', kwargs={'record_id': item.raa_lamning}) + f'#kommentarer-{item.hashid}'

    def item_title(self, item):
        return str(item)

    def item_description(self, item):
        return item.content

    def item_author_name(self, item):
        return item.user.username

    def item_pubdate(self, item):
        return item.created_time

    def items(self):
        return Comment.objects.filter(hidden=False).filter(comment_type='SR').exclude(raa_lamning__isnull=True).order_by('-created_time')[:50]
