from rest_framework import serializers
from ..models import ReadingContent, Language

class ReadingContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingContent
        fields = [
            'id',
            'title',
            'content',
            'language',
            'level',
            'topic',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_content(self, value):
        if len(value) < 100:
            raise serializers.ValidationError("Content must be at least 100 characters long")
        return value