from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .notification_models import Notification
from .notification_serializers import NotificationSerializer
from .notification_utils import check_and_send_performance_reminders


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for user notifications"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return notifications for the authenticated user"""
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get all unread notifications"""
        unread = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(unread, many=True)
        return Response({
            'count': unread.count(),
            'notifications': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        from django.utils import timezone
        updated = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({
            'message': f'{updated} notifications marked as read',
            'count': updated
        })


class SendPerformanceRemindersView(APIView):
    """
    POST /api/notifications/send-performance-reminders/
    Trigger sending performance reminders to inactive athletes
    (Admin only)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Only allow admins to trigger this
        if request.user.role != 'admin':
            return Response(
                {"error": "Only admins can trigger performance reminders"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notifications_sent = check_and_send_performance_reminders()
        
        return Response({
            'message': f'Successfully sent {notifications_sent} performance reminders',
            'count': notifications_sent
        })
