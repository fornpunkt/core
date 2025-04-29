import os

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag
from playwright.sync_api import expect, sync_playwright


@tag("e2e")
class TestMainMap(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.firefox.launch(headless=False)
        cls.page = cls.browser.new_page()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.browser.close()
        cls.playwright.stop()

    def test_map_init(self):
        self.page.goto(f"{self.live_server_url}/karta")
        # wait for the map to initialize and for the url to change
        self.page.wait_for_load_state("networkidle")
        self.assertIn("#map=5.40/", self.page.url)

    def test_map_sidebar(self):
        self.page.goto(f"{self.live_server_url}/karta#map=13.43/2038112.07/7890087.26")
        self.page.wait_for_load_state("networkidle")
        self.page.get_by_title("Välj lager").click()
        expect(self.page.get_by_text("Kartans innehåll")).to_be_visible()
        self.page.get_by_label("Ortofoto 1949-1970", exact=True).click()
