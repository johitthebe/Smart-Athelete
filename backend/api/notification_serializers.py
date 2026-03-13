from rest_framework import serializers
from .notification_models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for user notifications"""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'notification_type', 'title', 'message',
            'link_type', 'link_id', 'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'read_at', 'created_at']
    
    def create(self, validated_data):
        """Create notification"""
        return Notification.objects.create(**validated_data)
