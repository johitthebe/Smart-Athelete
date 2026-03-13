from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class PerformanceReport(models.Model):
    """
    Performance reports that athletes can share with their coaches
    """
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('reviewed', 'Reviewed'),
        ('feedback_given', 'Feedback Given'),
    )
    
    athlete = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submitted_reports',
        help_text="Athlete who submitted the report"
    )
    coach = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_reports',
        help_text="Coach who receives the report"
    )
    
    # Report metadata
    title = models.CharField(
        max_length=200,
        help_text="Report title"
    )
    time_range = models.CharField(
        max_length=20,
        choices=(('week', 'Week'), ('month', 'Month'), ('year', 'Year')),
        default='month'
    )
    
    # Analytics data (stored as JSON)
    analytics_data = models.JSONField(
        help_text="Performance analytics data"
    )
    
    # Athlete's notes/comments
    athlete_notes = models.TextField(
        blank=True,
        help_text="Athlete's comments about their performance"
    )
    
    # Coach feedback
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    coach_feedback = models.TextField(
        blank=True,
        help_text="Coach's feedback on the report"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the coach reviewed the report"
    )
    
    # Timestamps
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the report was submitted"
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    class Meta:
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['athlete', 'submitted_at']),
            models.Index(fields=['coach', 'status']),
        ]
    
    def __str__(self):
        return f"{self.athlete.username} → {self.coach.username}: {self.title}"
    
    def mark_reviewed(self, feedback=''):
        """Mark report as reviewed with optional feedback"""
        from django.utils import timezone
        self.status = 'feedback_given' if feedback else 'reviewed'
        self.coach_feedback = feedback
        self.reviewed_at = timezone.now()
        self.save()
