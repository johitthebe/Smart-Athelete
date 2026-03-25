from rest_framework import serializers
from django.contrib.auth import get_user_model
from .coach_request_models import CoachRequest, CoachCapacityLog
from .models import CoachAthleteAssignment

User = get_user_model()


class AvailableCoachSerializer(serializers.ModelSerializer):
    """Serializer for browsing available coaches"""
    coach_name = serializers.SerializerMethodField()
    athlete_count = serializers.SerializerMethodField()
    capacity_available = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'coach_name', 'accepting_requests', 'max_athletes',
            'athlete_count', 'capacity_available'
        ]
    
    def get_coach_name(self, obj):
        return obj.get_full_name() or obj.username
    
    def get_athlete_count(self, obj):
        return CoachAthleteAssignment.objects.filter(coach=obj, is_active=True).count()
    
    def get_capacity_available(self, obj):
        if obj.max_athletes is None:
            return True
        current = self.get_athlete_count(obj)
        return current < obj.max_athletes


class CoachRequestSerializer(serializers.ModelSerializer):
    """Serializer for coach requests"""
    athlete_name = serializers.CharField(source='athlete.get_full_name', read_only=True)
    athlete_username = serializers.CharField(source='athlete.username', read_only=True)
    athlete_email = serializers.CharField(source='athlete.email', read_only=True)
    coach_name = serializers.CharField(source='coach.get_full_name', read_only=True)
    coach_username = serializers.CharField(source='coach.username', read_only=True)
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = CoachRequest
        fields = [
            'id', 'athlete', 'athlete_name', 'athlete_username', 'athlete_email',
            'coach', 'coach_name', 'coach_username',
            'message', 'status', 'rejection_reason',
            'requested_at', 'updated_at', 'expires_at', 'responded_at',
            'is_expired'
        ]
        read_only_fields = ['id', 'athlete', 'status', 'requested_at', 'updated_at', 'expires_at', 'responded_at']
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['athlete'] = request.user
        return super().create(validated_data)


class CoachCapacityStatusSerializer(serializers.Serializer):
    """Serializer for coach capacity status"""
    accepting_requests = serializers.BooleanField()
    max_athletes = serializers.IntegerField(allow_null=True)
    current_athletes = serializers.IntegerField()
    capacity_available = serializers.IntegerField()
    paused_at = serializers.DateTimeField(allow_null=True)
    pause_reason = serializers.CharField(allow_blank=True)
    pending_requests = serializers.IntegerField()


class CoachCapacityLogSerializer(serializers.ModelSerializer):
    """Serializer for capacity logs"""
    coach_name = serializers.CharField(source='coach.get_full_name', read_only=True)
    
    class Meta:
        model = CoachCapacityLog
        fields = ['id', 'coach', 'coach_name', 'action', 'athlete_count', 'reason', 'created_at']
        read_only_fields = ['id', 'created_at']


class MyAthleteSerializer(serializers.ModelSerializer):
    """Serializer for coach's assigned athletes"""
    athlete_name = serializers.CharField(source='athlete.get_full_name', read_only=True)
    athlete_username = serializers.CharField(source='athlete.username', read_only=True)
    athlete_email = serializers.CharField(source='athlete.email', read_only=True)
    recent_activity = serializers.SerializerMethodField()
    active_goals = serializers.SerializerMethodField()
    
    class Meta:
        model = CoachAthleteAssignment
        fields = [
            'id', 'athlete', 'athlete_name', 'athlete_username', 'athlete_email',
            'assigned_at', 'is_active', 'notes',
            'recent_activity', 'active_goals'
        ]
    
    def get_recent_activity(self, obj):
        from performance.models import PerformanceLog
        recent = PerformanceLog.objects.filter(athlete=obj.athlete).order_by('-date').first()
        if recent:
            return recent.date.isoformat()
        return None
    
    def get_active_goals(self, obj):
        from performance.models import Goal
        return Goal.objects.filter(athlete=obj.athlete, status='active').count()
