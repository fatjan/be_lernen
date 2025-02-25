from django.db import migrations

def create_default_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model('api', 'SubscriptionPlan')
    UserProfile = apps.get_model('api', 'UserProfile')
    
    # Check if plans already exist to avoid duplicates
    if not SubscriptionPlan.objects.filter(code='free').exists():
        # Create Free Plan
        free_plan = SubscriptionPlan.objects.create(
            name='Free Plan',
            code='free',
            price=0.00,
            currency='USD',
            description='Basic features with limited words',
            max_words=50,
            features={
                'max_words': 50,
                'basic_features': True,
                'premium_features': False
            },
            is_active=True
        )
        
        # Only update profiles that don't have a subscription
        UserProfile.objects.filter(subscription__isnull=True).update(subscription=free_plan)
    
    # Create other plans only if they don't exist
    if not SubscriptionPlan.objects.filter(code='basic').exists():
        SubscriptionPlan.objects.create(
            name='Basic Plan',
            code='basic',
            price=9.99,
            currency='USD',
            description='Enhanced features with more words',
            max_words=500,
            features={
                'max_words': 500,
                'basic_features': True,
                'premium_features': False
            },
            is_active=True
        )

    if not SubscriptionPlan.objects.filter(code='premium').exists():
        SubscriptionPlan.objects.create(
            name='Premium Plan',
            code='premium',
            price=19.99,
            currency='USD',
            description='Full access to all features',
            max_words=999999,
            features={
                'max_words': 'unlimited',
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