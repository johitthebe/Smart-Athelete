from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):
    """
    Notifications for users about various events
    """
    TYPE_CHOICES = (
        ('feedback_received', 'Feedback Received'),
        ('goal_achieved', 'Goal Achieved'),
        ('coach_assigned', 'Coach Assigned'),
        ('message_received', 'Message Received'),
        ('report_reviewed', 'Report Reviewed'),
        ('performance_reminder', 'Performance Reminder'),
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="User who receives this notification"
    )
    
    notification_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        help_text="Type of notification"
    )
    
    title = models.CharField(
        max_length=200,
        help_text="Notification title"
    )
    
    message = models.TextField(
        help_text="Notification message"
    )
    
    # Link to related object
    link_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of linked object (Feedback, Goal, Message, etc.)"
    )
    
    link_id = models.IntegerField(
        null=True,
        blank=True,
        help_text="ID of the linked object"
    )
    
    # Status
    is_read = models.BooleanField(
        default=False,
        help_text="Whether notification has been read"
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification was read"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When notification was created"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
