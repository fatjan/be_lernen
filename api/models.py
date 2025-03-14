from django.db import models
from django.contrib.auth.models import User

class Language(models.Model):
    """Model to represent a language, e.g. English or German"""
    code = models.CharField(max_length=10, unique=True)  # e.g., 'en' for English, 'de' for German
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name'] 

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

class SubscriptionPlan(models.Model):
    PLAN_FREE = 'free'
    PLAN_BASIC = 'basic'
    PLAN_PREMIUM = 'premium'
    
    PLAN_CHOICES = [
        (PLAN_FREE, 'Free'),
        (PLAN_BASIC, 'Basic'),
        (PLAN_PREMIUM, 'Premium'),
    ]

    CURRENCY_CHOICES = [
        ('IDR', 'Indonesian Rupiah'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
    ]

    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='USD'
    )
    description = models.TextField(blank=True)
    max_words = models.IntegerField(default=100)
    features = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.currency} {self.price})"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    onboarded = models.BooleanField(default=False)
    preferred_language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    subscription = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True, default=None)
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    words_count = models.JSONField(default=dict) 

    def get_words_count(self, language_code):
        return self.words_count.get(language_code, 0)

    def increment_words_count(self, language_code):
        current_count = self.words_count.get(language_code, 0)
        self.words_count[language_code] = current_count + 1
        self.save()

    def decrement_words_count(self, language_code):
        current_count = self.words_count.get(language_code, 0)
        if current_count > 0:
            self.words_count[language_code] = current_count - 1
            self.save()

    def can_add_word(self, language_code):
        if not self.subscription:
            return False
        current_count = self.get_words_count(language_code)
        return current_count < self.subscription.max_words

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

    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,  # Won't delete feedback if user is deleted
        related_name='feedbacks',
        null=True,
        blank=True
    )
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

class Exercise(models.Model):
    EXERCISE_TYPES = [
        ('reading', 'Reading Comprehension'),
        ('grammar', 'Grammar Exercise'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('A1', 'Beginner'),
        ('A2', 'Elementary'),
        ('B1', 'Intermediate'),
        ('B2', 'Upper Intermediate'),
        ('C1', 'Advanced'),
        ('C2', 'Mastery'),
    ]

    title = models.CharField(max_length=200)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    exercise_type = models.CharField(max_length=20, choices=EXERCISE_TYPES)
    difficulty_level = models.CharField(max_length=2, choices=DIFFICULTY_LEVELS)
    content = models.TextField()  # Store the exercise content (text or grammar rules)
    instructions = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ExerciseQuestion(models.Model):
    exercise = models.ForeignKey(Exercise, related_name='questions', on_delete=models.CASCADE)
    question_text = models.TextField()
    correct_answer = models.TextField()
    options = models.JSONField(default=list)  # For multiple choice questions
    explanation = models.TextField(blank=True)
    order = models.IntegerField(default=0)

class UserExerciseProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    score = models.IntegerField(default=0)
    answers = models.JSONField(default=dict)  # Store user's answers
    completed_at = models.DateTimeField(null=True, blank=True)

class ReadingContent(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    language = models.ForeignKey(Language, related_name='readings', on_delete=models.CASCADE)
    level = models.CharField(max_length=2, choices=[
        ('A1', 'A1'),
        ('A2', 'A2'),
        ('B1', 'B1'),
        ('B2', 'B2'),
    ])
    topic = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['language']),
            models.Index(fields=['language', 'level']),  # Compound index for common filtering
        ]

    def __str__(self):
        return f"{self.title} ({self.language.name} - {self.level})"
    
    @classmethod
    def create_reading(cls, title, content, language_code, level, topic=None):
        """
        Create a reading content manually
        
        Args:
            title (str): Title of the reading
            content (str): Main content text
            language_code (str): Language code (e.g., 'en', 'de')
            level (str): Difficulty level (A1, A2, B1, B2)
            topic (str, optional): Topic category
            
        Returns:
            ReadingContent: Created reading content instance
        """
        try:
            language = Language.objects.get(code=language_code)
            return cls.objects.create(
                title=title,
                content=content,
                language=language,
                level=level,
                topic=topic
            )
        except Language.DoesNotExist:
            raise ValueError(f"Language with code '{language_code}' does not exist")

class ExerciseResult(models.Model):
    EXERCISE_TYPES = [
        ('matching', 'Matching'),
        ('reading', 'Reading Comprehension'),
        ('grammar', 'Grammar'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exercise_type = models.CharField(max_length=20, choices=EXERCISE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(auto_now=True)
    correct_answers = models.IntegerField(default=0)
    incorrect_answers = models.IntegerField(default=0)
    score = models.FloatField()  # Percentage score
    language = models.ForeignKey('Language', on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-created_at']

    def calculate_score(self):
        total = self.correct_answers + self.incorrect_answers
        return (self.correct_answers / total * 100) if total > 0 else 0

    def save(self, *args, **kwargs):
        self.score = self.calculate_score()
        super().save(*args, **kwargs)