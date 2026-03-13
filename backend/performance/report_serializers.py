from rest_framework import serializers
from .report_models import PerformanceReport
from django.contrib.auth import get_user_model

User = get_user_model()


class PerformanceReportSerializer(serializers.ModelSerializer):
    athlete_name = serializers.CharField(source='athlete.get_full_name', read_only=True)
    athlete_username = serializers.CharField(source='athlete.username', read_only=True)
    coach_name = serializers.CharField(source='coach.get_full_name', read_only=True)
    coach_username = serializers.CharField(source='coach.username', read_only=True)

    class Meta:
        model = PerformanceReport
        fields = [
            'id', 'athlete', 'athlete_name', 'athlete_username',
            'coach', 'coach_name', 'coach_username',
            'title', 'time_range', 'analytics_data', 'athlete_notes',
            'status', 'coach_feedback', 'reviewed_at',
            'submitted_at', 'updated_at'
        ]
        read_only_fields = ['id', 'athlete', 'status', 'reviewed_at', 'submitted_at', 'updated_at']

    def create(self, validated_data):
        # Set athlete from request context
        request = self.context.get('request')
        validated_data['athlete'] = request.user
        return super().create(validated_data)


class PerformanceReportListSerializer(serializers.ModelSerializer):
    """Simplified serializer for report lists"""
    athlete_name = serializers.CharField(source='athlete.get_full_name', read_only=True)
    coach_name = serializers.CharField(source='coach.get_full_name', read_only=True)
    has_feedback = serializers.SerializerMethodField()

    class Meta:
        model = PerformanceReport
        fields = [
            'id', 'athlete', 'athlete_name', 'coach', 'coach_name',
            'title', 'time_range', 'status', 'has_feedback',
            'submitted_at', 'reviewed_at'
        ]

    def get_has_feedback(self, obj):
        return bool(obj.coach_feedback)
