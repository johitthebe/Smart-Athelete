"""
Utility functions for creating and managing notifications
"""
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from .notification_models import Notification
from performance.models import PerformanceLog

User = get_user_model()


def send_performance_reminder(athlete):
    """
    Send a performance reminder notification to an athlete
    
    Args:
        athlete: User object with role='athlete'
    
    Returns:
        Notification object if created, None if already exists
    """
    now = timezone.now()
    yesterday = now - timedelta(hours=24)
    
    # Check if we already sent a reminder today
    existing_reminder = Notification.objects.filter(
        user=athlete,
        notification_type='performance_reminder',
        created_at__gte=yesterday
    ).exists()
    
    if not existing_reminder:
        notification = Notification.objects.create(
            user=athlete,
            notification_type='performance_reminder',
            title='Time to Log Your Performance',
            message='You haven\'t logged any performance in the last 24 hours. Keep track of your progress by logging your workouts!',
            link_type='performance_log',
            link_id=None
        )
        return notification
    
    return None


def check_and_send_performance_reminders():
    """
    Check all athletes and send reminders to those who haven't logged in 24 hours
    
    Returns:
        int: Number of reminders sent
    """
    now = timezone.now()
    yesterday = now - timedelta(hours=24)
    
    # Get all athletes
    athletes = User.objects.filter(role='athlete')
    
    notifications_sent = 0
    
    for athlete in athletes:
        # Check if athlete has logged any performance in the last 24 hours
        recent_logs = PerformanceLog.objects.filter(
            athlete=athlete,
            created_at__gte=yesterday
        ).exists()
        
        if not recent_logs:
            notification = send_performance_reminder(athlete)
            if notification:
                notifications_sent += 1
    
    return notifications_sent


def create_notification(user, notification_type, title, message, link_type=None, link_id=None):
    """
    Create a notification for a user
    
    Args:
        user: User object
        notification_type: Type of notification (must be in TYPE_CHOICES)
        title: Notification title
        message: Notification message
        link_type: Optional type of linked object
        link_id: Optional ID of linked object
    
    Returns:
        Notification object
    """
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        link_type=link_type or '',
        link_id=link_id
    )
