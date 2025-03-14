# Generated by Django 5.1.5 on 2025-02-27 00:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_feedback_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='words_count',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='subscription',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.subscriptionplan'),
        ),
    ]
