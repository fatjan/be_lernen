from django.db import models
from django.contrib.auth.models import User

class Language(models.Model):
    """Model to represent a language, e.g. English or German"""
    code = models.CharField(max_length=10, unique=True)  # e.g., 'en' for English, 'de' for German
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Word(models.Model):
    word = models.CharField(max_length=100)
    language = models.ForeignKey(Language, related_name='words', on_delete=models.CASCADE)
    plural_form = models.CharField(max_length=100, blank=True)
    translation = models.CharField(max_length=200, blank=True)
    part_of_speech = models.CharField(max_length=50, blank=True) # ex: noun, verb, etc.
    example_sentence = models.TextField(blank=True)
    gender = models.CharField(
        max_length=3, 
        choices=[('der', 'Masculine'), ('die', 'Feminine'), ('das', 'Neuter'), ('n/a', 'Not Applicable')], 
        default='n/a'
    )
    difficulty_level = models.CharField(
        max_length=50, 
        choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')], 
        default='medium'
    )
    category = models.CharField(max_length=50, blank=True) # ex: animal, action
    image_url = models.URLField(max_length=500, blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='word_entries')

    class Meta:
        indexes = [
            models.Index(fields=['user']),  
            models.Index(fields=['language']),  
            models.Index(fields=['user', 'language']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['user', 'language', 'word'], name='unique_word_per_user_language')
        ]
        ordering = ['added_at']

    def __str__(self):
        return self.word

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    onboarded = models.BooleanField(default=False)
    preferred_language = models.ForeignKey(Language, related_name='userprofiles', on_delete=models.SET_NULL, null=True)

class Feedback(models.Model):
    SATISFACTION_CHOICES = [
        (1, 'Very Dissatisfied'),
        (2, 'Dissatisfied'),
        (3, 'Neutral'),
        (4, 'Satisfied'),
        (5, 'Very Satisfied')
    ]

    RECOMMENDATION_CHOICES = [
        (1, 'Definitely Not'),
        (2, 'Probably Not'),
        (3, 'Maybe'),
        (4, 'Probably Yes'),
        (5, 'Definitely Yes')
    ]

    satisfaction_level = models.IntegerField(choices=SATISFACTION_CHOICES)
    would_recommend = models.IntegerField(choices=RECOMMENDATION_CHOICES)
    favorite_feature = models.CharField(max_length=100)
    most_challenging = models.CharField(max_length=100)
    feature_requests = models.TextField()
    improvement_suggestions = models.TextField()
    learning_goals = models.TextField()
    interface_rating = models.IntegerField(choices=SATISFACTION_CHOICES)
    willing_to_be_contacted = models.BooleanField(default=False)
    contact_email = models.EmailField(blank=True, null=True)
    contact_whatsapp = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']