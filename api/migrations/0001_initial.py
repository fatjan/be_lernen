# Generated by Django 5.1.5 on 2025-02-02 03:45

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10, unique=True)),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Word',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('word', models.CharField(max_length=100)),
                ('plural_form', models.CharField(blank=True, max_length=100)),
                ('translation', models.CharField(blank=True, max_length=200)),
                ('part_of_speech', models.CharField(blank=True, max_length=50)),
                ('example_sentence', models.TextField(blank=True)),
                ('gender', models.CharField(choices=[('der', 'Masculine'), ('die', 'Feminine'), ('das', 'Neuter'), ('n/a', 'Not Applicable')], default='n/a', max_length=3)),
                ('difficulty_level', models.CharField(choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')], default='medium', max_length=50)),
                ('category', models.CharField(blank=True, max_length=50)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('language', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='words', to='api.language')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='word_entries', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['added_at'],
                'indexes': [models.Index(fields=['user'], name='api_word_user_id_91692b_idx'), models.Index(fields=['language'], name='api_word_languag_8814a5_idx'), models.Index(fields=['user', 'language'], name='api_word_user_id_4f3388_idx')],
                'constraints': [models.UniqueConstraint(fields=('user', 'language', 'word'), name='unique_word_per_user_language')],
            },
        ),
    ]
