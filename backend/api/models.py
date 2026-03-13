from django.db import models
from accounts.models import User
from .notification_models import Notification


class AdminNotification(models.Model):
    """Model to store notifications for admin users about coach credential submissions"""
    NOTIFICATION_TYPES = (
        ('coach_credentials_submitted', 'Coach Credentials Submitted'),
        ('coach_resubmitted', 'Coach Resubmitted Credentials'),
    )
    
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    coach = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.notification_type} - {self.coach.get_full_name()}"
