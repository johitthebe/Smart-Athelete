from rest_framework import serializers
from .models import Goal, Benchmark, PerformanceLog, ActivityType
from .feedback_models import CoachFeedback
from django.utils import timezone


class ActivityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityType
        fields = ['id', 'name', 'icon', 'requires_distance', 'requires_duration', 'created_at']
        read_only_fields = ['id', 'created_at']


class BenchmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benchmark
        fields = [
            'id', 'benchmark_type', 'athlete_name', 'event', 'level', 
            'benchmark_value', 'unit', 'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        # If benchmark_type is 'athlete', athlete_name is required
        if data.get('benchmark_type') == 'athlete' and not data.get('athlete_name'):
            raise serializers.ValidationError({
                'athlete_name': 'Athlete name is required for athlete benchmarks'
            })
        return data


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
    best_performance = serializers.SerializerMethodField()
    gap_to_target = serializers.SerializerMethodField()
    athlete_name = serializers.CharField(source='athlete.get_full_name', read_only=True)

    class Meta:
        model = Goal
        fields = [
            'id', 'athlete', 'athlete_name', 'name', 'description',
            'activity_type', 'activity_type_id', 'event',
            'target_metric', 'target_value', 'target_unit', 'current_value',
            'benchmark', 'benchmark_id', 'deadline', 'status',
            'progress', 'log_count', 'best_performance', 'gap_to_target',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'athlete', 'athlete_name', 'current_value', 'created_at', 'updated_at', 
            'progress', 'log_count', 'best_performance', 'gap_to_target',
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
    
    def get_best_performance(self, obj):
        """Get the best single performance for this goal"""
        if not obj.logs.exists():
            return None
        
        # Get the best performance based on target metric
        if obj.target_metric == 'distance' and obj.logs.filter(distance__isnull=False).exists():
            best_log = obj.logs.filter(distance__isnull=False).order_by('-distance').first()
            return round(best_log.distance, 2) if best_log else None
        elif obj.target_metric == 'duration' and obj.logs.filter(duration__isnull=False).exists():
            best_log = obj.logs.filter(duration__isnull=False).order_by('-duration').first()
            return round(best_log.duration / 60, 2) if best_log else None  # Convert to minutes
        elif obj.target_metric == 'calories' and obj.logs.filter(calories__isnull=False).exists():
            best_log = obj.logs.filter(calories__isnull=False).order_by('-calories').first()
            return best_log.calories if best_log else None
        
        return None
    
    def get_gap_to_target(self, obj):
        """Calculate gap between best performance and target"""
        best = self.get_best_performance(obj)
        if best is None:
            return None
        
        gap = obj.target_value - best
        return round(gap, 2) if gap > 0 else 0

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
            'date', 'duration', 'distance', 'calories', 'intensity',
            'intensity_level', 'perceived_effort', 'weather', 'terrain', 'how_felt',
            'notes', 'date_logged', 'created_at', 'is_personal_best',
        ]
        read_only_fields = ['athlete', 'athlete_name', 'goal_name', 'created_at', 'date_logged', 'is_personal_best']

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
        goal = validated_data.get('goal')
        
        # Detect if this is a personal best
        is_pb = False
        if goal:
            target_metric = goal.target_metric
            new_value = None
            
            # Get the value for the target metric
            if target_metric == 'distance' and validated_data.get('distance'):
                new_value = validated_data['distance']
            elif target_metric == 'duration' and validated_data.get('duration'):
                new_value = validated_data['duration']
            elif target_metric == 'calories' and validated_data.get('calories'):
                new_value = validated_data['calories']
            
            # Check if this is a personal best
            if new_value is not None:
                # Get all previous logs for this goal
                previous_logs = PerformanceLog.objects.filter(
                    goal=goal,
                    athlete=validated_data['athlete']
                )
                
                # Find the previous best value
                previous_best = None
                if target_metric == 'distance':
                    previous_best_log = previous_logs.filter(distance__isnull=False).order_by('-distance').first()
                    previous_best = previous_best_log.distance if previous_best_log else None
                elif target_metric == 'duration':
                    previous_best_log = previous_logs.filter(duration__isnull=False).order_by('-duration').first()
                    previous_best = previous_best_log.duration if previous_best_log else None
                elif target_metric == 'calories':
                    previous_best_log = previous_logs.filter(calories__isnull=False).order_by('-calories').first()
                    previous_best = previous_best_log.calories if previous_best_log else None
                
                # This is a PB if there's no previous best, or if new value is better
                if previous_best is None or new_value > previous_best:
                    is_pb = True
                    validated_data['is_personal_best'] = True
                    
                    # Mark previous PB as no longer PB
                    if previous_best is not None:
                        if target_metric == 'distance':
                            previous_logs.filter(distance=previous_best, is_personal_best=True).update(is_personal_best=False)
                        elif target_metric == 'duration':
                            previous_logs.filter(duration=previous_best, is_personal_best=True).update(is_personal_best=False)
                        elif target_metric == 'calories':
                            previous_logs.filter(calories=previous_best, is_personal_best=True).update(is_personal_best=False)
        
        return super().create(validated_data)



class CoachFeedbackSerializer(serializers.ModelSerializer):
    coach_name = serializers.CharField(source='coach.get_full_name', read_only=True)
    athlete_name = serializers.CharField(source='athlete.get_full_name', read_only=True)
    performance_log_details = serializers.SerializerMethodField()
    goal_details = serializers.SerializerMethodField()
    
    class Meta:
        model = CoachFeedback
        fields = [
            'id', 'coach', 'coach_name', 'athlete', 'athlete_name',
            'feedback_type', 'title', 'message',
            'performance_log', 'performance_log_details',
            'goal', 'goal_details',
            'is_read', 'read_at', 'is_acknowledged', 'acknowledged_at',
            'rating',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'coach', 'coach_name', 'athlete_name', 'is_read', 'read_at',
            'is_acknowledged', 'acknowledged_at', 'created_at', 'updated_at'
        ]
    
    def get_performance_log_details(self, obj):
        if obj.performance_log:
            return {
                'id': obj.performance_log.id,
                'date': obj.performance_log.date,
                'activity': obj.performance_log.activity_type.name if obj.performance_log.activity_type else obj.performance_log.event,
            }
        return None
    
    def get_goal_details(self, obj):
        if obj.goal:
            return {
                'id': obj.goal.id,
                'name': obj.goal.name,
                'progress': round(obj.goal.progress_percentage(), 2)
            }
        return None
    
    def validate(self, data):
        # Validate title and message
        if not data.get('title'):
            raise serializers.ValidationError({'title': 'Feedback title is required'})
        if not data.get('message'):
            raise serializers.ValidationError({'message': 'Feedback message is required'})
        
        # Validate athlete exists
        if not data.get('athlete'):
            raise serializers.ValidationError({'athlete': 'Athlete is required'})
        
        return data
    
    def create(self, validated_data):
        validated_data['coach'] = self.context['request'].user
        feedback = super().create(validated_data)
        
        # Create notification for athlete
        from api.notification_utils import create_notification
        coach_name = self.context['request'].user.get_full_name() or self.context['request'].user.username
        
        create_notification(
            user=feedback.athlete,
            notification_type='feedback_received',
            title=f'New feedback from {coach_name}',
            message=f'{coach_name} provided feedback: "{feedback.title}"',
            link_type='feedback',
            link_id=feedback.id
        )
        
        return feedback


from .ai_models import SuggestedGoal, SuggestedWorkout


class SuggestedGoalSerializer(serializers.ModelSerializer):
    athlete_name = serializers.CharField(source='athlete.get_full_name', read_only=True)
    actual_goal_details = serializers.SerializerMethodField()
    
    class Meta:
        model = SuggestedGoal
        fields = [
            'id', 'athlete', 'athlete_name',
            'event', 'target_value', 'unit', 'deadline_weeks',
            'difficulty_level', 'reasoning', 'training_required', 'key_tip',
            'status', 'actual_goal', 'actual_goal_details',
            'suggested_at', 'responded_at'
        ]
        read_only_fields = [
            'athlete', 'athlete_name', 'actual_goal', 'actual_goal_details',
            'suggested_at', 'responded_at'
        ]
    
    def get_actual_goal_details(self, obj):
        if obj.actual_goal:
            return {
                'id': obj.actual_goal.id,
                'name': obj.actual_goal.name,
                'progress': round(obj.actual_goal.progress_percentage(), 2)
            }
        return None


class SuggestedWorkoutSerializer(serializers.ModelSerializer):
    athlete_name = serializers.CharField(source='athlete.get_full_name', read_only=True)
    actual_log_details = serializers.SerializerMethodField()
    
    class Meta:
        model = SuggestedWorkout
        fields = [
            'id', 'athlete', 'athlete_name',
            'workout_type', 'name', 'description',
            'target_value', 'target_unit', 'intensity', 'estimated_duration',
            'reasoning', 'benefit',
            'status', 'actual_log', 'actual_log_details',
            'suggested_at', 'added_at', 'completed_at'
        ]
        read_only_fields = [
            'athlete', 'athlete_name', 'actual_log', 'actual_log_details',
            'suggested_at', 'added_at', 'completed_at'
        ]
    
    def get_actual_log_details(self, obj):
        if obj.actual_log:
            return {
                'id': obj.actual_log.id,
                'date': obj.actual_log.date,
                'distance': obj.actual_log.distance,
                'duration': obj.actual_log.duration
            }
        return None
