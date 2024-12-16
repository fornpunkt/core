import json

import requests
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Check the map layers search file for broken links"

    def handle(self, *args, **options):
        with open("./core/static/map-layers.json") as f:
            data = json.load(f)

            broken_links = set()
            for layer in data:
                if not "docs" in layer:
                    continue

                # TODO: ensure that no layers have empty docs (property should be removed instead)
                if layer["docs"] is None or layer["docs"] == "":
                    print(f"Warning found emptly docs for layer: {layer['display_name']}")
                    continue

                if layer["docs"] in broken_links:
                    continue

                try:
                    response = requests.get(layer["docs"])
                    if (
                        response.status_code != 200
                    ):  # NOTE: a valid non-200 response still indicates that the intended target should be updated
                        broken_links.add(layer["docs"])
                except requests.exceptions.RequestException as e:
                    print(f'Fatal error checking link: {layer["docs"]}, for {layer["display_name"]}', e)

            if broken_links:
                print("The following links appear to be broken:")
                for link in broken_links:
                    print(link)
            else:
                print("All links appear to be valid")
