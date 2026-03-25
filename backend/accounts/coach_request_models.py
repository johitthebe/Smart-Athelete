from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class CoachRequest(models.Model):
    """
    Tracks athlete requests to coaches
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    )
    
    athlete = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='coach_requests_sent',
        limit_choices_to={'role': 'athlete'}
    )
    coach = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='coach_requests_received',
        limit_choices_to={'role': 'coach'}
    )
    message = models.TextField(
        blank=True,
        help_text="Optional message from athlete to coach"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    rejection_reason = models.TextField(
        blank=True,
        help_text="Coach's reason for rejection"
    )
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        help_text="Auto-expire after 7 days"
    )
    responded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When coach accepted/rejected"
    )
    
    class Meta:
        ordering = ['-requested_at']
        unique_together = [['athlete', 'coach', 'status']]
        indexes = [
            models.Index(fields=['coach', 'status']),
            models.Index(fields=['athlete', 'status']),
            models.Index(fields=['status', 'expires_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['athlete', 'coach'],
                condition=models.Q(status='pending'),
                name='unique_pending_request'
            )
        ]
    
    def __str__(self):
        return f"{self.athlete.username} → {self.coach.username} ({self.status})"
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return self.status == 'pending' and timezone.now() > self.expires_at


class CoachCapacityLog(models.Model):
    """
    Tracks coach capacity changes (pause/resume/auto-pause)
    """
    ACTION_CHOICES = (
        ('paused', 'Manually Paused'),
        ('resumed', 'Manually Resumed'),
        ('auto_paused', 'Auto-Paused (Capacity Reached)'),
    )
    
    coach = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='capacity_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    athlete_count = models.IntegerField(
        help_text="Number of athletes at time of action"
    )
    reason = models.TextField(
        blank=True,
        help_text="Reason for pause/resume"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['coach', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.coach.username} - {self.action} at {self.created_at}"
