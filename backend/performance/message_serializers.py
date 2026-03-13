from rest_framework import serializers
from .message_models import Message
from django.contrib.auth import get_user_model

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    recipient_name = serializers.CharField(source='recipient.get_full_name', read_only=True)
    recipient_username = serializers.CharField(source='recipient.username', read_only=True)
    reply_count = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'sender_name', 'sender_username',
            'recipient', 'recipient_name', 'recipient_username',
            'subject', 'body', 'is_read', 'read_at', 'created_at',
            'parent_message', 'reply_count'
        ]
        read_only_fields = ['id', 'sender', 'is_read', 'read_at', 'created_at']

    def get_reply_count(self, obj):
        return obj.replies.count()

    def create(self, validated_data):
        # Set sender from request context
        request = self.context.get('request')
        validated_data['sender'] = request.user
        return super().create(validated_data)


class MessageListSerializer(serializers.ModelSerializer):
    """Simplified serializer for message lists"""
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    recipient_name = serializers.CharField(source='recipient.get_full_name', read_only=True)
    preview = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'sender_name', 'recipient', 'recipient_name',
            'subject', 'preview', 'is_read', 'created_at'
        ]

    def get_preview(self, obj):
        """Return first 100 characters of body"""
        return obj.body[:100] + '...' if len(obj.body) > 100 else obj.body
