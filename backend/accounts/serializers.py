from rest_framework import serializers
from accounts.models import User, AthleteProfile
from datetime import date

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "first_name", "last_name", "role"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user

from accounts.models import CoachCredential, CoachApproval


class CoachCredentialSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    coach_name = serializers.CharField(source='coach.get_full_name', read_only=True)
    
    class Meta:
        model = CoachCredential
        fields = ['id', 'coach', 'coach_name', 'credential_type', 'credential_name', 
                  'issuing_organization', 'issue_date', 'file', 'file_url', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at', 'file_url', 'coach_name']
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class CoachApprovalSerializer(serializers.ModelSerializer):
    coach_name = serializers.CharField(source='coach.get_full_name', read_only=True)
    coach_email = serializers.EmailField(source='coach.email', read_only=True)
    coach_username = serializers.CharField(source='coach.username', read_only=True)
    credentials = CoachCredentialSerializer(source='coach.credentials', many=True, read_only=True)
    credential_count = serializers.SerializerMethodField()
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = CoachApproval
        fields = ['id', 'coach', 'coach_name', 'coach_email', 'coach_username', 'status', 
                  'rejection_reason', 'reviewed_by', 'reviewed_by_name', 'reviewed_at', 
                  'created_at', 'updated_at', 'credentials', 'credential_count']
        read_only_fields = ['id', 'coach', 'created_at', 'updated_at', 'reviewed_by', 'reviewed_at']
    
    def get_credential_count(self, obj):
        return obj.coach.credentials.count()


from accounts.models import CoachAthleteAssignment


class CoachAthleteAssignmentSerializer(serializers.ModelSerializer):
    coach_name = serializers.CharField(source='coach.get_full_name', read_only=True)
    coach_email = serializers.EmailField(source='coach.email', read_only=True)
    coach_username = serializers.CharField(source='coach.username', read_only=True)
    athlete_name = serializers.CharField(source='athlete.get_full_name', read_only=True)
    athlete_email = serializers.EmailField(source='athlete.email', read_only=True)
    athlete_username = serializers.CharField(source='athlete.username', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = CoachAthleteAssignment
        fields = [
            'id', 'coach', 'coach_name', 'coach_email', 'coach_username',
            'athlete', 'athlete_name', 'athlete_email', 'athlete_username',
            'assigned_by', 'assigned_by_name', 'assigned_at', 'is_active', 'notes'
        ]
        read_only_fields = ['id', 'assigned_by', 'assigned_at']
    
    def validate(self, data):
        # Ensure coach has coach role
        if data['coach'].role != 'coach':
            raise serializers.ValidationError("Selected user is not a coach")
        
        # Ensure athlete has athlete role
        if data['athlete'].role != 'athlete':
            raise serializers.ValidationError("Selected user is not an athlete")
        
        # Prevent self-assignment
        if data['coach'] == data['athlete']:
            raise serializers.ValidationError("Cannot assign a user to themselves")
        
        return data



class AthleteProfileSerializer(serializers.ModelSerializer):
    """Serializer for athlete onboarding profile"""
    
    class Meta:
        model = AthleteProfile
        fields = [
            'id', 'user',
            # Step 1: Account & Profile
            'age', 'gender', 'height', 'height_unit', 'weight', 'weight_unit', 'body_type',
            # Step 2: Fitness Background
            'fitness_level', 'primary_sport', 'years_training', 'current_performance_baseline',
            # Step 3: Goals
            'primary_goal', 'goal_timeframe', 'target_event', 'target_event_date',
            # Step 4: Training Preferences
            'weekly_availability', 'preferred_intensity', 'preferred_training_time', 'equipment_access',
            # Step 5: Health & Motivation
            'injury_history', 'medical_conditions', 'current_activity_level', 'motivation_level', 'guidance_preference',
            # Timestamps
            'completed_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'completed_at', 'updated_at']
    
    def validate_age(self, value):
        """Validate age is between 13 and 120"""
        if value < 13 or value > 120:
            raise serializers.ValidationError("Age must be between 13 and 120")
        return value
    
    def validate_height(self, value):
        """Validate height is positive"""
        if value <= 0:
            raise serializers.ValidationError("Height must be greater than 0")
        return value
    
    def validate_weight(self, value):
        """Validate weight is positive"""
        if value <= 0:
            raise serializers.ValidationError("Weight must be greater than 0")
        return value
    
    def validate_weekly_availability(self, value):
        """Validate weekly availability is between 1 and 7"""
        if value < 1 or value > 7:
            raise serializers.ValidationError("Weekly availability must be between 1 and 7 days")
        return value
    
    def validate_motivation_level(self, value):
        """Validate motivation level is between 1 and 10"""
        if value < 1 or value > 10:
            raise serializers.ValidationError("Motivation level must be between 1 and 10")
        return value
    
    def validate_target_event_date(self, value):
        """Validate target event date is in the future"""
        if value and value < date.today():
            raise serializers.ValidationError("Target event date must be in the future")
        return value
    
    def validate_equipment_access(self, value):
        """Validate equipment access is a list"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Equipment access must be a list")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        # Ensure user is an athlete
        user = self.context['request'].user
        if user.role != 'athlete':
            raise serializers.ValidationError("Only athletes can create profiles")
        
        # Check if profile already exists for this user
        if not self.instance and AthleteProfile.objects.filter(user=user).exists():
            raise serializers.ValidationError("Profile already exists for this user")
        
        return data
    
    def create(self, validated_data):
        """Create profile with authenticated user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
