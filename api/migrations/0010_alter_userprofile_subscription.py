# Generated by Django 5.1.5 on 2025-02-24 23:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_alter_userprofile_subscription'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='subscription',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subscribers', to='api.subscriptionplan'),
        ),
    ]
