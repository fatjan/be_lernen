from . import serializers
from ..models import Feedback

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = [
            'id',
            'satisfaction_level',
            'would_recommend',
            'favorite_feature',
            'most_challenging',
            'feature_requests',
            'improvement_suggestions',
            'learning_goals',
            'interface_rating',
            'willing_to_be_contacted',
            'contact_email',
            'contact_whatsapp',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate(self, data):
        if data.get('willing_to_be_contacted'):
            if not data.get('contact_email') and not data.get('contact_whatsapp'):
                raise serializers.ValidationError(
                    "Either email or WhatsApp number is required when willing to be contacted is true"
                )
        return data