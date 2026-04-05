from django.contrib import admin
from .models import ActivityType, Benchmark, Goal, PerformanceLog


@admin.register(ActivityType)
class ActivityTypeAdmin(admin.ModelAdmin):
    list_display = ['icon', 'name', 'requires_distance', 'requires_duration', 'created_at']
    list_filter = ['requires_distance', 'requires_duration']
    search_fields = ['name']


@admin.register(Benchmark)
class BenchmarkAdmin(admin.ModelAdmin):
    list_display = ['benchmark_type', 'athlete_name', 'event', 'level', 'benchmark_value', 'unit', 'created_at']
    list_filter = ['benchmark_type', 'level', 'event']
    search_fields = ['athlete_name', 'event', 'level']
    ordering = ['benchmark_type', 'event', 'level']
    
    fieldsets = (
        ('Benchmark Information', {
            'fields': ('benchmark_type', 'athlete_name', 'event', 'level')
        }),
        ('Performance Data', {
            'fields': ('benchmark_value', 'unit', 'description')
        }),
    )


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ['name', 'athlete', 'status', 'progress_display', 'target_value', 'target_unit', 'deadline', 'created_at']
    list_filter = ['status', 'target_metric', 'created_at']
    search_fields = ['name', 'athlete__username', 'athlete__first_name', 'athlete__last_name']
    readonly_fields = ['current_value', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Goal Information', {
            'fields': ('athlete', 'name', 'description', 'status')
        }),
        ('Activity Details', {
            'fields': ('activity_type', 'event', 'benchmark')
        }),
        ('Target & Progress', {
            'fields': ('target_metric', 'target_value', 'target_unit', 'current_value', 'deadline')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def progress_display(self, obj):
        return f"{obj.progress_percentage():.1f}%"
    progress_display.short_description = 'Progress'


@admin.register(PerformanceLog)
class PerformanceLogAdmin(admin.ModelAdmin):
    list_display = ['athlete', 'goal', 'activity_type', 'date', 'distance', 'duration', 'calories', 'intensity', 'created_at']
    list_filter = ['date', 'activity_type', 'intensity', 'created_at']
    search_fields = ['athlete__username', 'goal__name', 'event', 'notes']
    readonly_fields = ['created_at', 'date_logged']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Log Information', {
            'fields': ('athlete', 'goal', 'activity_type', 'event', 'date')
        }),
        ('Performance Metrics', {
            'fields': ('value', 'distance', 'duration', 'calories', 'intensity')
        }),
        ('Additional Information', {
            'fields': ('notes', 'date_logged', 'created_at'),
            'classes': ('collapse',)
        }),
    )


from .feedback_models import CoachFeedback

@admin.register(CoachFeedback)
class CoachFeedbackAdmin(admin.ModelAdmin):
    list_display = ['coach', 'athlete', 'feedback_type', 'title', 'is_read', 'is_acknowledged', 'created_at']
    list_filter = ['feedback_type', 'is_read', 'is_acknowledged', 'created_at']
    search_fields = ['coach__username', 'athlete__username', 'title', 'message']
    readonly_fields = ['created_at', 'updated_at', 'read_at', 'acknowledged_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Feedback Information', {
            'fields': ('coach', 'athlete', 'feedback_type', 'title', 'message')
        }),
        ('Associations', {
            'fields': ('performance_log', 'goal'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'is_acknowledged', 'acknowledged_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


from .ai_models import SuggestedGoal, SuggestedWorkout

@admin.register(SuggestedGoal)
class SuggestedGoalAdmin(admin.ModelAdmin):
    list_display = ['athlete', 'event', 'target_value', 'unit', 'difficulty_level', 'status', 'suggested_at']
    list_filter = ['status', 'difficulty_level', 'suggested_at']
    search_fields = ['athlete__username', 'event', 'reasoning']
    readonly_fields = ['suggested_at', 'responded_at']
    
    fieldsets = (
        ('Goal Details', {
            'fields': ('athlete', 'event', 'target_value', 'unit', 'deadline_weeks')
        }),
        ('AI Analysis', {
            'fields': ('difficulty_level', 'reasoning', 'training_required', 'key_tip')
        }),
        ('Status', {
            'fields': ('status', 'actual_goal', 'suggested_at', 'responded_at')
        }),
    )


@admin.register(SuggestedWorkout)
class SuggestedWorkoutAdmin(admin.ModelAdmin):
    list_display = ['athlete', 'name', 'workout_type', 'intensity', 'status', 'suggested_at']
    list_filter = ['status', 'workout_type', 'suggested_at']
    search_fields = ['athlete__username', 'name', 'description']
    readonly_fields = ['suggested_at', 'added_at', 'completed_at']
    
    fieldsets = (
        ('Workout Details', {
            'fields': ('athlete', 'workout_type', 'name', 'description')
        }),
        ('Target', {
            'fields': ('target_value', 'target_unit', 'intensity', 'estimated_duration')
        }),
        ('AI Analysis', {
            'fields': ('reasoning', 'benefit')
        }),
        ('Status', {
            'fields': ('status', 'actual_log', 'suggested_at', 'added_at', 'completed_at')
        }),
    )
