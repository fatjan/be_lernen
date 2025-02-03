from rest_framework import serializers
from .models import Word, User

class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = [
            'id', 
            'word', 
            'language', 
            'plural_form', 
            'translation', 
            'part_of_speech', 
            'example_sentence', 
            'gender', 
            'difficulty_level', 
            'category', 
            'added_at', 
            'updated_at', 
            'user'
        ]
        read_only_fields = ['id', 'added_at', 'updated_at', 'user']  # Make fields read-only

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email']
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email']
        )
        return user