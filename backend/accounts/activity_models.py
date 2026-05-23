from django.db import models
from django.conf import settings


class UserActivity(models.Model):
    """Track all user actions in the system"""
    
    ACTION_TYPES = (
        ('user_registered', 'User Registered'),
        ('user_login', 'User Login'),
        ('profile_updated', 'Profile Updated'),
        ('goal_created', 'Goal Created'),
        ('goal_updated', 'Goal Updated'),
        ('goal_completed', 'Goal Completed'),
        ('workout_logged', 'Workout Logged'),
        ('performance_logged', 'Performance Logged'),
        ('coach_request_sent', 'Coach Request Sent'),
        ('coach_request_accepted', 'Coach Request Accepted'),
        ('coach_request_rejected', 'Coach Request Rejected'),
        ('coach_approved', 'Coach Approved'),
        ('coach_rejected', 'Coach Rejected'),
        ('athlete_assigned', 'Athlete Assigned'),
        ('feedback_given', 'Feedback Given'),
        ('password_changed', 'Password Changed'),
        ('onboarding_completed', 'Onboarding Completed'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activities')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action_type', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name_plural = 'User Activities'
    
    def __str__(self):
        return f"{self.user.username} - {self.action_type} - {self.created_at}"
