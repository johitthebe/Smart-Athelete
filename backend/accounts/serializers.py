from rest_framework import serializers
from accounts.models import User

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
        read_only_fields = ['id', 'coach', 'uploaded_at', 'file_url', 'coach_name']
    
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
