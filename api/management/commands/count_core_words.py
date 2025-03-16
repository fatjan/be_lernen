from django.core.management.base import BaseCommand
from api.models import Word

class Command(BaseCommand):
    help = 'Count words where core is True'

    def handle(self, *args, **options):
        core_count = Word.objects.filter(core=True).count()
        self.stdout.write(self.style.SUCCESS(f'Number of core words: {core_count}'))