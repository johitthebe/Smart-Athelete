from django.conf import settings
from django.db import models
from django.utils import timezone


class ActivityType(models.Model):
    """Predefined activity types for performance logging"""
    name = models.CharField(max_length=50, unique=True)
    icon = models.CharField(max_length=10, default="🏃")  # Emoji icon
    requires_distance = models.BooleanField(default=True)
    requires_duration = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.icon} {self.name}"


class Benchmark(models.Model):
    event = models.CharField(max_length=100)
    level = models.CharField(
        max_length=50,
        default="general",
        help_text="e.g., U18, U20, Elite"
    )
    benchmark_value = models.FloatField(help_text="e.g., 4.6 for 40m sprint in seconds")
    unit = models.CharField(max_length=20, default="seconds", help_text="seconds, meters, etc")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event} ({self.level}): {self.benchmark_value}{self.unit}"


class Goal(models.Model):
    """Enhanced Goal model with activity type and detailed tracking"""
    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='goals'
    )
    name = models.CharField(max_length=200, help_text="Goal name, e.g., 'Run 5km in under 30 minutes'")
    description = models.TextField(blank=True, help_text="Detailed description of the goal")
    activity_type = models.ForeignKey(
        ActivityType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='goals'
    )
    
    # Legacy fields (keeping for backward compatibility)
    event = models.CharField(max_length=100, blank=True, help_text="e.g., 40m Sprint")
    
    # Target metrics
    target_metric = models.CharField(
        max_length=50,
        choices=(
            ('distance', 'Distance'),
            ('duration', 'Duration'),
            ('calories', 'Calories'),
            ('pace', 'Pace'),
        ),
        default='distance',
        help_text="Primary metric to track"
    )
    target_value = models.FloatField(help_text="Target value to achieve")
    target_unit = models.CharField(max_length=20, default="km", help_text="Unit of measurement")
    
    # Progress tracking
    current_value = models.FloatField(default=0.0, help_text="Current progress value")
    
    benchmark = models.ForeignKey(
        Benchmark,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='goals'
    )
    deadline = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=(
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('on_hold', 'On Hold'),
        ),
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['athlete', 'status']),
            models.Index(fields=['deadline']),
        ]

    def __str__(self):
        return f"{self.athlete.username} - {self.name}"

    def progress_percentage(self):
        """Calculate progress as percentage of target"""
        if self.target_value == 0:
            return 0
        return min((self.current_value / self.target_value) * 100, 100)

    def check_completion(self):
        """Check if goal is completed and update status"""
        if self.current_value >= self.target_value and self.status == 'active':
            self.status = 'completed'
            self.save()


class PerformanceLog(models.Model):
    """Enhanced Performance Log with goal association and detailed metrics"""
    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='performance_logs'
    )
    goal = models.ForeignKey(
        Goal,
        on_delete=models.CASCADE,
        related_name='logs',
        help_text="Associated goal for this performance log"
    )
    activity_type = models.ForeignKey(
        ActivityType,
        on_delete=models.SET_NULL,
        null=True,
        related_name='logs'
    )
    
    # Legacy fields
    event = models.CharField(max_length=100, blank=True, help_text="e.g., 40m Sprint")
    value = models.FloatField(null=True, blank=True, help_text="e.g., 4.9 seconds")
    
    # Date and duration
    date = models.DateField(help_text="Date of the activity")
    duration = models.IntegerField(null=True, blank=True, help_text="Duration in seconds")
    
    # Performance metrics
    distance = models.FloatField(null=True, blank=True, help_text="Distance in kilometers")
    heart_rate = models.IntegerField(null=True, blank=True, help_text="Average heart rate in BPM")
    calories = models.IntegerField(null=True, blank=True, help_text="Calories burned")
    power = models.IntegerField(null=True, blank=True, help_text="Average power in watts")
    pace = models.FloatField(null=True, blank=True, help_text="Pace in min/km")
    elevation = models.IntegerField(null=True, blank=True, help_text="Elevation gain in meters")
    
    intensity = models.IntegerField(
        default=5,
        help_text="1-10 scale"
    )
    notes = models.TextField(blank=True)
    date_logged = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['athlete', 'date']),
            models.Index(fields=['goal']),
            models.Index(fields=['activity_type']),
        ]

    def __str__(self):
        return f"{self.athlete.username} - {self.activity_type or self.event} on {self.date}"

    def save(self, *args, **kwargs):
        """Update goal progress when log is saved"""
        super().save(*args, **kwargs)
        
        # Update goal progress based on target metric
        if self.goal:
            if self.goal.target_metric == 'distance' and self.distance:
                # Sum all distances for this goal
                total_distance = PerformanceLog.objects.filter(
                    goal=self.goal
                ).aggregate(models.Sum('distance'))['distance__sum'] or 0
                self.goal.current_value = total_distance
            elif self.goal.target_metric == 'duration' and self.duration:
                # Sum all durations for this goal
                total_duration = PerformanceLog.objects.filter(
                    goal=self.goal
                ).aggregate(models.Sum('duration'))['duration__sum'] or 0
                self.goal.current_value = total_duration / 60  # Convert to minutes
            elif self.goal.target_metric == 'calories' and self.calories:
                # Sum all calories for this goal
                total_calories = PerformanceLog.objects.filter(
                    goal=self.goal
                ).aggregate(models.Sum('calories'))['calories__sum'] or 0
                self.goal.current_value = total_calories
            
            self.goal.check_completion()
            self.goal.save()

