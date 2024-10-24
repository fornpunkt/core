import csv
from io import StringIO

import requests

from django.core.management.base import BaseCommand, CommandError
from core.models import LamningWikipediaLink

class Command(BaseCommand):
    help = 'Import wikipedia links from remote CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_url', type=str)

    def handle(self, *args, **options):
        csv_url = options['csv_url']
        response = requests.get(csv_url)
        if response.status_code != 200:
            raise CommandError(f'Could not fetch CSV file from {csv_url}')

        buffer = StringIO(response.text)
        print(response.text)
        reader = csv.DictReader(buffer, fieldnames=['kmr', 'wikipedia'], skipinitialspace=True)

        self.stdout.write(self.style.WARNING(f'Note that this script isn\'t able to handle duplicate data, always check against existing data first.'))
        self.stdout.write(self.style.WARNING(f'Confirm import from {csv_url}'))
        confirm = input('Enter Y to confirm: ')
        if confirm.upper() != 'Y':
            raise CommandError('Import aborted')

        rows = list()
        for row in reader:
            rows.append(LamningWikipediaLink(kmr_lamning=row['kmr'], wikipedia=row['wikipedia']))
        LamningWikipediaLink.objects.bulk_create(rows, update_fields=['wikipedia', 'kmr_lamning'])

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {len(rows)} rows'))
