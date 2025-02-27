from django.db import migrations

def create_default_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model('api', 'SubscriptionPlan')
    UserProfile = apps.get_model('api', 'UserProfile')
    
    # First, set all existing profiles' subscription to NULL
    UserProfile.objects.all().update(subscription=None)
    
    # Create Free Plan
    free_plan = SubscriptionPlan.objects.create(
        name='Free Plan',
        code='free',
        price=0.00,
        currency='USD',
        description='Basic features with limited words',
        max_words=50,  # 50 words per language limit
        features={
            'max_words_per_language': 50,
            'basic_features': True,
            'premium_features': False
        },
        is_active=True
    )
    
    # Create Basic Plan
    SubscriptionPlan.objects.create(
        name='Basic Plan',
        code='basic',
        price=6.99,
        currency='USD',
        description='Enhanced features with more words',
        max_words=500,  # 500 words per language limit
        features={
            'max_words_per_language': 500,
            'basic_features': True,
            'premium_features': False
        },
        is_active=True
    )

    # Create Premium Plan
    SubscriptionPlan.objects.create(
        name='Premium Plan',
        code='premium',
        price=19.99,
        currency='USD',
        description='Full access to all features',
        max_words=999999,  # Effectively unlimited
        features={
            'max_words_per_language': 'unlimited',
            'basic_features': True,
            'premium_features': True
        },
        is_active=True
    )

def remove_default_plans(apps, schema_editor):
    # We'll keep this empty to preserve data when rolling back
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('api', '0009_alter_userprofile_subscription'),
    ]

    operations = [
        migrations.RunPython(create_default_plans, remove_default_plans),
    ]