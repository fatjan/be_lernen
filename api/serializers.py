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
    name = serializers.CharField(write_only=True, required=False)  # Accept `name` on input but don't include in output
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "name"]
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name": {"required": False},
        }
    
    def get_onboarded(self, obj):
        return getattr(obj.userprofile, 'onboarded', False)

    def create(self, validated_data):
        name = validated_data.pop("name", "")
        name_parts = name.strip().split(" ")

        validated_data["first_name"] = name_parts[0] if name_parts else ""
        validated_data["last_name"] = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        return super().create(validated_data)

    def update(self, instance, validated_data):
        name = validated_data.pop("name", None)
        if name:
            first_name, last_name = self.split_name(name)
            instance.first_name = first_name
            instance.last_name = last_name

        return super().update(instance, validated_data)

    def split_name(self, name):
        name_parts = name.strip().split(" ")
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        return first_name, last_name

    def to_representation(self, instance):
        """Override to_representation to add 'name' field in the response."""
        # Get the default representation
        representation = super().to_representation(instance)
        
        # Combine first_name and last_name into a single 'name' field
        representation['name'] = f"{instance.first_name} {instance.last_name}".strip()

        return representation