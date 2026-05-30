from django.conf import settings
from django.db import models
from django.utils import timezone


class SuggestedGoal(models.Model):
    """AI-suggested goals that athlete can accept/reject"""
    
    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='suggested_goals'
    )
    
    # Goal details
    event = models.CharField(max_length=200)
    target_value = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50)
    deadline_weeks = models.IntegerField()
    
    # Reasoning and difficulty
    DIFFICULTY_CHOICES = [
        ('conservative', 'Conservative'),
        ('recommended', 'Recommended'),
        ('ambitious', 'Ambitious'),
    ]
    difficulty_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='recommended'
    )
    reasoning = models.TextField()
    training_required = models.TextField()  # Changed from CharField to TextField
    key_tip = models.TextField()
    
    # Status
    STATUS_CHOICES = [
        ('pending', 'Waiting for Decision'),
        ('accepted', 'Accepted by Athlete'),
        ('rejected', 'Rejected by Athlete'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # If accepted, link to actual goal
    actual_goal = models.ForeignKey(
        'Goal',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='suggestion_source'
    )
    
    # Metadata
    suggested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-suggested_at']
        indexes = [
            models.Index(fields=['athlete', 'status']),
        ]
    
    def __str__(self):
        return f"{self.athlete.username} - {self.event}: {self.target_value}{self.unit} ({self.difficulty_level})"
    
    def accept(self):
        """Accept suggestion and create actual goal"""
        from .models import Goal
        from datetime import timedelta
        
        if self.status != 'pending':
            return None
        
        # Create actual goal
        deadline = timezone.now().date() + timedelta(weeks=self.deadline_weeks)
        goal = Goal.objects.create(
            athlete=self.athlete,
            name=f"{self.event} - {self.target_value}{self.unit}",
            description=f"AI Suggested Goal: {self.reasoning}",
            event=self.event,
            target_value=float(self.target_value),
            target_unit=self.unit,
            deadline=deadline,
            status='active'
        )
        
        self.actual_goal = goal
        self.status = 'accepted'
        self.responded_at = timezone.now()
        self.save()
        
        return goal
    
    def reject(self):
        """Reject suggestion"""
        self.status = 'rejected'
        self.responded_at = timezone.now()
        self.save()


class SuggestedWorkout(models.Model):
    """AI-suggested workouts that athlete can accept/reject"""
    
    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='suggested_workouts'
    )
    
    # Workout details
    WORKOUT_TYPE_CHOICES = [
        ('speed', 'Speed Work'),
        ('endurance', 'Endurance'),
        ('intervals', 'Intervals'),
        ('recovery', 'Recovery'),
    ]
    workout_type = models.CharField(
        max_length=20,
        choices=WORKOUT_TYPE_CHOICES
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Target
    target_value = models.DecimalField(max_digits=10, decimal_places=2)
    target_unit = models.CharField(max_length=50)
    intensity = models.CharField(max_length=20)
    estimated_duration = models.IntegerField(help_text="Duration in minutes")
    
    # Reasoning and benefits
    reasoning = models.TextField()
    benefit = models.CharField(max_length=200)
    
    # Status
    STATUS_CHOICES = [
        ('suggested', 'Suggested'),
        ('added_to_plan', 'Added to Training Plan'),
        ('completed', 'Completed'),
        ('dismissed', 'Dismissed'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='suggested'
    )
    
    # If completed, link to actual log
    actual_log = models.ForeignKey(
        'PerformanceLog',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='suggestion_source'
    )
    
    # Metadata
    suggested_at = models.DateTimeField(auto_now_add=True)
    added_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-suggested_at']
        indexes = [
            models.Index(fields=['athlete', 'status']),
        ]
    
    def __str__(self):
        return f"{self.athlete.username} - {self.name} ({self.workout_type})"
    
    def add_to_plan(self):
        """Add workout to training plan"""
        if self.status == 'suggested':
            self.status = 'added_to_plan'
            self.added_at = timezone.now()
            self.save()
    
    def mark_completed(self, performance_log):
        """Mark workout as completed and link to log"""
        self.status = 'completed'
        self.actual_log = performance_log
        self.completed_at = timezone.now()
        self.save()
    
    def dismiss(self):
        """Dismiss suggestion"""
        self.status = 'dismissed'
        self.save()
