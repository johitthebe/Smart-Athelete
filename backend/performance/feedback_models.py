from django.conf import settings
from django.db import models
from django.utils import timezone


class CoachFeedback(models.Model):
    """Feedback from coaches to athletes"""
    FEEDBACK_TYPE_CHOICES = (
        ('general', 'General Feedback'),
        ('performance', 'Performance Review'),
        ('goal', 'Goal-Specific'),
        ('technique', 'Technique Improvement'),
        ('motivation', 'Motivational'),
    )
    
    coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='given_feedback'
    )
    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_feedback'
    )
    feedback_type = models.CharField(
        max_length=20,
        choices=FEEDBACK_TYPE_CHOICES,
        default='general'
    )
    title = models.CharField(max_length=200, help_text="Brief title for the feedback")
    message = models.TextField(help_text="Detailed feedback message")
    
    # Optional associations
    performance_log = models.ForeignKey(
        'PerformanceLog',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedback'
    )
    goal = models.ForeignKey(
        'Goal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedback'
    )
    
    # Status tracking
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['athlete', 'is_read']),
            models.Index(fields=['coach', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.coach.username} → {self.athlete.username}: {self.title}"
    
    def mark_as_read(self):
        """Mark feedback as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
