# Generated by Django 5.1.5 on 2025-02-20 10:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_feedback'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='feedback',
            name='user',
        ),
    ]
