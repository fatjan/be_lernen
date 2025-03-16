from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Update words_count for a specific user'

    def handle(self, *args, **options):
        try:
            user = User.objects.get(id=1)
            user_profile = user.userprofile
            user_profile.words_count['jp'] = 150
            user_profile.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully updated words_count for user {user.username}'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User with ID 1 does not exist'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))