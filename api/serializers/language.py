from . import serializers
from ..models import Language

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = [
            "id",
            "code",
            "name",
        ]
        read_only_fields = ["id"]
    def validate(self, data):
        if not data.get('code'):
            raise serializers.ValidationError("Language code is required")
        return data