from . import serializers
from django.utils import timezone


class GoogleAuthSerializer(serializers.Serializer):
    credential = serializers.DictField()

    def validate(self, data):
        credential = data.get('credential', {})
        if not credential.get('access_token'):
            raise serializers.ValidationError({
                'error': 'Missing token',
                'message': 'Google access token is required'
            })
        return data

    def update_last_login(self, user):
        current_time = timezone.now()
        user.last_login = current_time
        user.save(update_fields=['last_login'])