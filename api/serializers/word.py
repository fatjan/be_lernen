from . import serializers
from ..models import Word

class WordSerializer(serializers.ModelSerializer):
    def validate(self, data):
        user_profile = self.context['request'].user.userprofile
        language_code = data['language'].code

        if not user_profile.can_add_word(language_code):
            max_words = user_profile.subscription.max_words if user_profile.subscription else 50
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