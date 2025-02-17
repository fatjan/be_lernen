from rest_framework import serializers
from .models import Word, User, Language

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

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name']
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
    
    def get_onboarded(self, obj):
        return getattr(obj.userprofile, 'onboarded', False)
