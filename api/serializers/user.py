from ..models import User, UserProfile
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone

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
                    current_time = timezone.now()
                    user.last_login = current_time
                    user.save(update_fields=['last_login'])
                    
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