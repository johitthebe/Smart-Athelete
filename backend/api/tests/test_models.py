from django.test import TestCase
from django.contrib.auth import get_user_model
from api.models import AdminNotification

User = get_user_model()


class AdminNotificationModelTest(TestCase):
    """Test the AdminNotification model"""
    
    def setUp(self):
        self.coach = User.objects.create_user(
            username='testcoach',
            email='coach@test.com',
            password='testpass123',
            role='coach_pending'
        )
    
    def test_create_admin_notification(self):
        """Test creating an admin notification"""
        notification = AdminNotification.objects.create(
            notification_type='coach_credentials_submitted',
            coach=self.coach,
            message='Coach testcoach has submitted credentials for review'
        )
        
        self.assertEqual(notification.notification_type, 'coach_credentials_submitted')
        self.assertEqual(notification.coach, self.coach)
        self.assertFalse(notification.is_read)
        self.assertIsNotNone(notification.created_at)
    
    def test_mark_notification_as_read(self):
        """Test marking a notification as read"""
        notification = AdminNotification.objects.create(
            notification_type='coach_credentials_submitted',
            coach=self.coach,
            message='Test message'
        )
        
        self.assertFalse(notification.is_read)
        
        notification.is_read = True
        notification.save()
        
        self.assertTrue(notification.is_read)
    
    def test_notification_ordering(self):
        """Test that notifications are ordered by created_at descending"""
        notification1 = AdminNotification.objects.create(
            notification_type='coach_credentials_submitted',
            coach=self.coach,
            message='First notification'
        )
        
        notification2 = AdminNotification.objects.create(
            notification_type='coach_resubmitted',
            coach=self.coach,
            message='Second notification'
        )
        
        notifications = AdminNotification.objects.all()
        self.assertEqual(notifications[0], notification2)
        self.assertEqual(notifications[1], notification1)
