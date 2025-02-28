from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Word, User, Language, UserProfile, Feedback, SubscriptionPlan, ExerciseQuestion, Exercise, UserExerciseProgress

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = [
            "id",
            "code",
            "name",
        ]
        read_only_fields = ["id"]

class WordSerializer(serializers.ModelSerializer):
    def validate(self, data):
        user_profile = self.context['request'].user.userprofile
        language_code = data['language'].code

        if not user_profile.can_add_word(language_code):
            max_words = user_profile.subscription.max_words if user_profile.subscription else 0
            raise serializers.ValidationError(
                f"Word limit reached for {language_code}. Maximum {max_words} words allowed per language with your current plan."
            )
        return data

    def create(self, validated_data):
        word = super().create(validated_data)
        self.context['request'].user.userprofile.increment_words_count(word.language.code)
        return word

    def delete(self, instance):
        language_code = instance.language.code
        instance.delete()
        self.context['request'].user.userprofile.decrement_words_count(language_code)
    class Meta:
        model = Word
        fields = [
            "id", 
            "word", 
            "language", 
            "plural_form", 
            "translation", 
            "part_of_speech", 
            "example_sentence", 
            "gender", 
            "difficulty_level", 
            "category", 
            "image_url", 
            "added_at", 
            "updated_at", 
            "user"
        ]
        read_only_fields = ["id", "added_at", "updated_at"]
        extra_kwargs = {
            'word': {'required': True},
            'language': {'required': True},
            'translation': {'required': True},
            'user': {'required': True},
            'plural_form': {'required': False},
            'part_of_speech': {'required': False},
            'example_sentence': {'required': False},
            'gender': {'required': False},
            'difficulty_level': {'required': False},
            'category': {'required': False},
            'image_url': {'required': False},
        }

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    name = serializers.CharField(write_only=True)  # Add name field

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'name']
    
    def create(self, validated_data):
        # Extract and split name
        name = validated_data.pop('name', '')
        name_parts = name.strip().split(" ")
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email'],
            first_name=first_name,
            last_name=last_name,
        )
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    onboarded = serializers.SerializerMethodField(read_only=True)
    preferred_language = serializers.SerializerMethodField(read_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    # Update last_login with debug prints
                    from django.utils import timezone
                    current_time = timezone.now()
                    user.last_login = current_time
                    user.save(update_fields=['last_login'])
                    
                    # Rest of the function remains the same
                    UserProfile.objects.get_or_create(user=user)
                    data['user'] = user
                    return data
                raise serializers.ValidationError('User account is disabled.')
            raise serializers.ValidationError('Unable to log in with provided credentials.')
        raise serializers.ValidationError('Must include "username" and "password".')
    
    def get_onboarded(self, obj):
        user = obj['user'] if isinstance(obj, dict) else obj
        try:
            profile = UserProfile.objects.get(user=user)
            return profile.onboarded
        except UserProfile.DoesNotExist:
            return False

    def get_preferred_language(self, obj):
        user = obj['user'] if isinstance(obj, dict) else obj
        try:
            profile = UserProfile.objects.get(user=user)
            return profile.preferred_language.code if profile.preferred_language else None
        except (UserProfile.DoesNotExist, AttributeError):
            return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user = instance['user'] if isinstance(instance, dict) else instance
        if user:
            representation.update({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            })
        return representation

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'code', 'price', 'description', 'max_words', 'features']

class UserProfileDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    preferred_language = serializers.SerializerMethodField()
    subscription_code = serializers.SerializerMethodField()  # Add this field

    class Meta:
        model = User
        fields = [
            "id", 
            "username", 
            "email", 
            "name", 
            "preferred_language",
            "subscription_code",  # Add this to fields
        ]
        read_only_fields = ["id", "username", "email"]

    def get_subscription_code(self, obj):
        try:
            return obj.userprofile.subscription.code if obj.userprofile.subscription else None
        except AttributeError:
            return None

    def get_preferred_language(self, obj):
        try:
            return obj.userprofile.preferred_language.code if obj.userprofile.preferred_language else None
        except AttributeError:
            return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.first_name or instance.last_name:
            representation['name'] = f"{instance.first_name} {instance.last_name}".strip()
        return representation

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    preferred_language = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "first_name", 
            "last_name", 
            "name", 
            "email",
            "preferred_language",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Add preferred language to the response
        try:
            representation['preferred_language'] = instance.userprofile.preferred_language.code if instance.userprofile.preferred_language else None
        except (UserProfile.DoesNotExist, AttributeError):
            representation['preferred_language'] = None
        
        # Add name to the response
        if instance.first_name or instance.last_name:
            representation['name'] = f"{instance.first_name} {instance.last_name}".strip()
        
        return representation

    def update(self, instance, validated_data):
        # Ensure UserProfile exists
        userprofile, created = UserProfile.objects.get_or_create(user=instance)
        
        # Handle preferred language update
        preferred_language_code = validated_data.pop('preferred_language', None)
        if preferred_language_code:
            try:
                language_instance = Language.objects.get(code=preferred_language_code)
                userprofile.preferred_language = language_instance
                userprofile.save()
            except Language.DoesNotExist:
                raise serializers.ValidationError(f"Language with code '{preferred_language_code}' does not exist")
    
        # Handle name update
        name = validated_data.pop("name", None)
        if name:
            first_name, last_name = self.split_name(name)
            instance.first_name = first_name
            instance.last_name = last_name
            instance.save()
    
        return instance

    def split_name(self, name):
        name_parts = name.strip().split(" ")
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        return first_name, last_name

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = [
            'id',
            'satisfaction_level',
            'would_recommend',
            'favorite_feature',
            'most_challenging',
            'feature_requests',
            'improvement_suggestions',
            'learning_goals',
            'interface_rating',
            'willing_to_be_contacted',
            'contact_email',
            'contact_whatsapp',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate(self, data):
        if data.get('willing_to_be_contacted'):
            if not data.get('contact_email') and not data.get('contact_whatsapp'):
                raise serializers.ValidationError(
                    "Either email or WhatsApp number is required when willing to be contacted is true"
                )
        return data

class GoogleAuthSerializer(serializers.Serializer):
    credential = serializers.DictField()

    def validate(self, data):
        credential = data.get('credential', {})
        if not credential.get('access_token'):
            raise serializers.ValidationError({
                'error': 'Missing token',
                'message': 'Google access token is required'
            })
        return data

    def update_last_login(self, user):
        from django.utils import timezone
        current_time = timezone.now()
        user.last_login = current_time
        user.save(update_fields=['last_login'])

class ExerciseQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseQuestion
        fields = [
            'id',
            'question_text',
            'options',
            'correct_answer',
            'explanation',
            'order'
        ]

    def validate_options(self, value):
        if not isinstance(value, list) or len(value) < 2:
            raise serializers.ValidationError("At least 2 options are required")
        return value

class UserExerciseProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserExerciseProgress
        fields = ['id', 'completed', 'score', 'answers', 'completed_at']

class ExerciseSerializer(serializers.ModelSerializer):
    questions = ExerciseQuestionSerializer(many=True, read_only=True)
    user_progress = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = [
            'id',
            'title',
            'language',
            'exercise_type',
            'difficulty_level',
            'content',
            'instructions',
            'questions',
            'user_progress',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            progress = UserExerciseProgress.objects.filter(
                user=request.user,
                exercise=obj
            ).first()
            if progress:
                return UserExerciseProgressSerializer(progress).data
        return None

    def validate(self, data):
        if data['exercise_type'] == 'reading' and len(data['content']) < 100:
            raise serializers.ValidationError("Reading exercises must have content of at least 100 characters")
        return data

    def create(self, validated_data):
        questions_data = self.context.get('questions', [])
        exercise = Exercise.objects.create(**validated_data)
        
        for idx, question_data in enumerate(questions_data):
            question_data['order'] = idx + 1
            ExerciseQuestion.objects.create(exercise=exercise, **question_data)
            
        return exercise

    def check_answers(self, user_answers):
        exercise = self.instance
        correct_count = 0
        total_questions = exercise.questions.count()
        results = []

        for question in exercise.questions.all():
            user_answer = user_answers.get(str(question.id))
            is_correct = user_answer == question.correct_answer
            if is_correct:
                correct_count += 1
            
            results.append({
                'question_id': question.id,
                'correct': is_correct,
                'explanation': question.explanation if is_correct else None
            })

        score = int((correct_count / total_questions) * 100) if total_questions > 0 else 0

        return {
            'score': score,
            'correct_count': correct_count,
            'total_questions': total_questions,
            'results': results
        }