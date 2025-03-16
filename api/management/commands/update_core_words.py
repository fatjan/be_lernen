from django.core.management.base import BaseCommand
from api.models import Word

class Command(BaseCommand):
    help = 'Update core field for specific word IDs'

    def handle(self, *args, **options):
        word_ids = range(148, 159)  # This will include IDs 148 to 158
        updated = Word.objects.filter(id__in=word_ids).update(core=True)
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated} words'))