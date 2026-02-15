from rest_framework import serializers
from .models import Goal, Benchmark, PerformanceLog, ActivityType
from django.utils import timezone


class ActivityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityType
        fields = ['id', 'name', 'icon', 'requires_distance', 'requires_duration', 'created_at']
        read_only_fields = ['id', 'created_at']


class BenchmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benchmark
        fields = ['id', 'event', 'level', 'benchmark_value', 'unit', 'created_at']


class GoalSerializer(serializers.ModelSerializer):
    benchmark = BenchmarkSerializer(read_only=True)
    benchmark_id = serializers.PrimaryKeyRelatedField(
        queryset=Benchmark.objects.all(),
        write_only=True,
        required=False,
        source='benchmark',
        allow_null=True
    )
    activity_type = ActivityTypeSerializer(read_only=True)
    activity_type_id = serializers.PrimaryKeyRelatedField(
        queryset=ActivityType.objects.all(),
        write_only=True,
        required=False,
        source='activity_type',
        allow_null=True
    )
    progress = serializers.SerializerMethodField()
    log_count = serializers.SerializerMethodField()
    athlete_name = serializers.CharField(source='athlete.get_full_name', read_only=True)

    class Meta:
        model = Goal
        fields = [
            'id', 'athlete', 'athlete_name', 'name', 'description',
            'activity_type', 'activity_type_id', 'event',
            'target_metric', 'target_value', 'target_unit', 'current_value',
            'benchmark', 'benchmark_id', 'deadline', 'status',
            'progress', 'log_count', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'athlete', 'athlete_name', 'current_value', 'created_at', 'updated_at', 'progress', 'log_count',
        ]

    def get_progress(self, obj):
        return {
            'percentage': round(obj.progress_percentage(), 2),
            'is_completed': obj.status == 'completed',
            'current_value': obj.current_value,
            'target_value': obj.target_value,
            'remaining': max(obj.target_value - obj.current_value, 0),
        }
    
    def get_log_count(self, obj):
        return obj.logs.count()

    def validate(self, data):
        # Validate required fields
        if not data.get('name'):
            raise serializers.ValidationError({'name': 'Goal name is required'})
        if not data.get('target_value'):
            raise serializers.ValidationError({'target_value': 'Target value is required'})
        if not data.get('deadline'):
            raise serializers.ValidationError({'deadline': 'Deadline is required'})
        
        # Validate target value is positive
        if data.get('target_value') and data['target_value'] <= 0:
            raise serializers.ValidationError({'target_value': 'Target value must be positive'})
        
        return data

    def create(self, validated_data):
        validated_data['athlete'] = self.context['request'].user
        return super().create(validated_data)


class PerformanceLogSerializer(serializers.ModelSerializer):
    activity_type = ActivityTypeSerializer(read_only=True)
    activity_type_id = serializers.PrimaryKeyRelatedField(
        queryset=ActivityType.objects.all(),
        write_only=True,
        required=False,
        source='activity_type',
        allow_null=True
    )
    goal_name = serializers.CharField(source='goal.name', read_only=True)
    athlete_name = serializers.CharField(source='athlete.get_full_name', read_only=True)

    class Meta:
        model = PerformanceLog
        fields = [
            'id', 'athlete', 'athlete_name', 'goal', 'goal_name',
            'activity_type', 'activity_type_id', 'event', 'value',
            'date', 'duration', 'distance', 'heart_rate', 'calories',
            'power', 'pace', 'elevation', 'intensity', 'notes',
            'date_logged', 'created_at',
        ]
        read_only_fields = ['athlete', 'athlete_name', 'goal_name', 'created_at', 'date_logged']

    def validate(self, data):
        # Validate goal is required
        if not data.get('goal'):
            raise serializers.ValidationError({'goal': 'Goal is required for performance logging'})
        
        # Validate goal belongs to the athlete
        request = self.context.get('request')
        if request and data.get('goal'):
            if data['goal'].athlete != request.user:
                raise serializers.ValidationError({'goal': 'You can only log performance for your own goals'})
            
            # Validate goal is active
            if data['goal'].status != 'active':
                raise serializers.ValidationError({'goal': 'You can only log performance for active goals'})
        
        # Validate date is not in the future
        if data.get('date') and data['date'] > timezone.now().date():
            raise serializers.ValidationError({'date': 'Performance date cannot be in the future'})
        
        # Validate at least one metric is provided
        metrics = ['distance', 'duration', 'calories']
        if not any(data.get(metric) for metric in metrics):
            raise serializers.ValidationError(
                'At least one performance metric (distance, duration, or calories) is required'
            )
        
        # Validate positive numeric values
        numeric_fields = ['duration', 'distance', 'heart_rate', 'calories', 'power', 'pace', 'elevation']
        for field in numeric_fields:
            if data.get(field) is not None and data[field] < 0:
                raise serializers.ValidationError({field: f'{field.capitalize()} must be a positive number'})
        
        return data

    def create(self, validated_data):
        validated_data['athlete'] = self.context['request'].user
        return super().create(validated_data)

