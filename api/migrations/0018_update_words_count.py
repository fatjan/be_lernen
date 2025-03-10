from django.db import migrations

def update_words_count(apps, schema_editor):
    UserProfile = apps.get_model('api', 'UserProfile')
    for profile in UserProfile.objects.all():
        if not profile.words_count:  # if empty dict or None
            profile.words_count = {'de': 0, 'en': 0, 'jp': 0}
            profile.save()

def reverse_words_count(apps, schema_editor):
    UserProfile = apps.get_model('api', 'UserProfile')
    for profile in UserProfile.objects.all():
        profile.words_count = {}
        profile.save()

class Migration(migrations.Migration):
    dependencies = [
        ('api', '0017_alter_readingcontent_language_and_more'),  # Replace this with your actual previous migration name
    ]

    operations = [
        migrations.RunPython(update_words_count, reverse_words_count),
    ]