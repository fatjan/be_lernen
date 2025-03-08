from ..models import User, UserProfile
from . import serializers
from ..models import Language

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