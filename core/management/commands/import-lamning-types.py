from csv import DictReader
from django.core.management import BaseCommand

from core.models import KMRLamningType

class Command(BaseCommand):
    help = 'Populates db with data from kmr_types.csv'

    def handle(self, *args, **options):
        if KMRLamningType.objects.exists():
           print('Data already loaded...exiting.')
           return

        for row in DictReader(open('./kmr_types.csv')):
            lamnings_type = KMRLamningType(name=row['name'], raa_id=row['raa_id'], slug=row['slug'], description=row['description'])
            lamnings_type.save()
