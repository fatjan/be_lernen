from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Word, User, Language, UserProfile

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
                    # Create UserProfile if it doesn't exist
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

class UserProfileDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    preferred_language = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", 
            "username", 
            "email", 
            "name", 
            "preferred_language",
        ]
        read_only_fields = ["id", "username", "email"]

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

    def update(self, instance, validated_data):
        # Ensure UserProfile exists
        print('update validated_data: ', validated_data)
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