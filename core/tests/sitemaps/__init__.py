from django.test import TestCase
from django.urls import reverse

class SitemapTest(TestCase):
    '''Tests of the sitemap'''

    def test_sitemap(self):
        '''Tests that the sitemap is generated correctly'''
        response = self.client.get(reverse('django.contrib.sitemaps.views.sitemap'))
        self.assertEqual(response.status_code, 200)
        # /karta is a static page, so it should allways be in the sitemap
        self.assertContains(response, '/karta</loc>')
