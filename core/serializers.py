from rest_framework import serializers
from .models import SiteFeedback


class SiteFeedbackSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())


    class Meta:
        model = SiteFeedback
        fields = ['id', 'user', 'message', 'rating', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']