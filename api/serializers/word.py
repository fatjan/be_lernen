from . import serializers
from ..models import Word

class WordSerializer(serializers.ModelSerializer):
    def validate(self, data):
        user_profile = self.context['request'].user.userprofile
        language_code = data['language'].code

        # Initialize language in words_count if it doesn't exist
        if language_code not in user_profile.words_count:
            user_profile.words_count[language_code] = 0
            user_profile.save()

        max_words, can_add_word = self.can_add_word(user_profile, language_code)
        if not can_add_word:
            raise serializers.ValidationError(
                f"Word limit reached for {language_code}. Maximum {max_words} words allowed per language with your current plan."
            )
        return data
    
    def can_add_word(self, user_profile, language_code):
        max_words = 50  # default max words
        current_count = user_profile.words_count.get(language_code, 0)
        return max_words, current_count < max_words

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
            "user",
            "core",
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
            'core': {'required': False},
        }