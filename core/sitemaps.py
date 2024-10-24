from django.contrib.flatpages.sitemaps import FlatPageSitemap
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import CustomTag, KMRLamningType, Lamning


class StaticViewSitemap(Sitemap):
    '''Sitemap for public pages without, without being powered by the database.'''

    def items(self):
        return ['dashboard', 'map', 'tag_list', 'raa_type_list', 'observationtypes']

    def location(self, item):
        return reverse(item)

class LamningSitemap(Sitemap):
    '''Sitemap for FP-lamnings'''

    def items(self):
        return Lamning.objects.filter(hidden=False)

    def lastmod(self, obj):
        return obj.changed_time

class TagSitemap(Sitemap):
    '''Sitemap for tags'''

    def items(self):
        return CustomTag.objects.all().order_by('slug')

    def location(self, item):
        return reverse('tag', kwargs={'slug': item.slug})

class RaaTypeSitemap(Sitemap):
    '''Sitemap for RAA types'''

    def items(self):
        return KMRLamningType.objects.all().order_by('slug')

    def location(self, item):
        return reverse('raa_type', kwargs={'slug': item.slug})

sitemaps = {
    'lamnings': LamningSitemap,
    'tags': TagSitemap,
    'raa_types': RaaTypeSitemap,
    'static': StaticViewSitemap,
    'flatpages': FlatPageSitemap,
}
