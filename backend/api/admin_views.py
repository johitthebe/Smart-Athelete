"""
Admin-specific views for user and system management
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Q, Count

from .serializers import UserSerializer, AdminUserSerializer

User = get_user_model()


def is_admin(user):
    """Check if user is admin"""
    return user.role == "admin" or user.is_superuser


class AdminUserViewSet(viewsets.ModelViewSet):
    """
    Admin-only viewset for managing users
    Supports CRUD operations on all users
    """
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Only admins can access this"""
        if not is_admin(self.request.user):
            return User.objects.none()
        
        queryset = User.objects.all().order_by('-date_joined')
        
        # Filter by role
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role)
        
        # Search by username or email
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) | 
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """List all users with stats"""
        if not is_admin(request.user):
            return Response(
                {"error": "Only admins can access user management"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().list(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        """Create new user"""
        if not is_admin(request.user):
            return Response(
                {"error": "Only admins can create users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Update user"""
        if not is_admin(request.user):
            return Response(
                {"error": "Only admins can update users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete user"""
        print(f"Delete request from user: {request.user.username}, role: {getattr(request.user, 'role', 'NO ROLE')}, is_admin: {is_admin(request.user)}")
        
        if not is_admin(request.user):
            return Response(
                {"error": "Only admins can delete users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Prevent admin from deleting themselves
        user = self.get_object()
        if user.id == request.user.id:
            return Response(
                {"error": "You cannot delete your own account"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get user statistics"""
        if not is_admin(request.user):
            return Response(
                {"error": "Only admins can view stats"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        total_users = User.objects.count()
        athletes = User.objects.filter(role='athlete').count()
        coaches = User.objects.filter(role='coach').count()
        admins = User.objects.filter(role='admin').count()
        pending_coaches = User.objects.filter(role='coach_pending').count()
        
        return Response({
            'total_users': total_users,
            'athletes': athletes,
            'coaches': coaches,
            'admins': admins,
            'pending_coaches': pending_coaches,
        })
    
    @action(detail=True, methods=['post'])
    def change_role(self, request, pk=None):
        """Change user's role"""
        if not is_admin(request.user):
            return Response(
                {"error": "Only admins can change roles"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        new_role = request.data.get('role')
        
        if not new_role:
            return Response(
                {"error": "Role is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        valid_roles = ['athlete', 'coach', 'coach_pending', 'admin']
        if new_role not in valid_roles:
            return Response(
                {"error": f"Invalid role. Must be one of: {', '.join(valid_roles)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.role = new_role
        user.save()
        
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Activate or deactivate user"""
        if not is_admin(request.user):
            return Response(
                {"error": "Only admins can activate/deactivate users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = self.get_object()
        
        # Prevent admin from deactivating themselves
        if user.id == request.user.id:
            return Response(
                {"error": "You cannot deactivate your own account"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.is_active = not user.is_active
        user.save()
        
        serializer = self.get_serializer(user)
        return Response(serializer.data)


from rest_framework.views import APIView
from accounts.models import CoachApproval, CoachCredential
from accounts.serializers import CoachApprovalSerializer
from api.models import AdminNotification
from api.serializers import AdminNotificationSerializer
from django.utils import timezone


class PendingCoachesListView(APIView):
    """
    API endpoint for admins to view pending coach applications
    GET /api/admin/coaches/pending/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not is_admin(request.user):
            return Response(
                {"error": "Only admins can view pending coaches"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get coaches with pending status who have submitted credentials
        pending_approvals = CoachApproval.objects.filter(
            status='pending',
            coach__credentials__isnull=False
        ).distinct().order_by('-coach__credentials__uploaded_at')
        
        serializer = CoachApprovalSerializer(pending_approvals, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CoachDetailView(APIView):
    """
    API endpoint for admins to view coach details
    GET /api/admin/coaches/<id>/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        if not is_admin(request.user):
            return Response(
                {"error": "Only admins can view coach details"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            approval = CoachApproval.objects.get(coach_id=pk)
            serializer = CoachApprovalSerializer(approval, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CoachApproval.DoesNotExist:
            return Response(
                {"error": "Coach not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class ApproveCoachView(APIView):
    """
    API endpoint for admins to approve a coach
    POST /api/admin/coaches/<id>/approve/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        if not is_admin(request.user):
            return Response(
                {"error": "Only admins can approve coaches"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            approval = CoachApproval.objects.get(coach_id=pk)
            
            # Update approval status
            approval.status = 'approved'
            approval.reviewed_by = request.user
            approval.reviewed_at = timezone.now()
            approval.save()
            
            # Update user role
            coach = approval.coach
            coach.role = 'coach'
            coach.save()
            
            # Remove admin notifications for this coach
            AdminNotification.objects.filter(coach=coach).delete()
            
            # TODO: Send approval email (will implement in task 7)
            
            serializer = CoachApprovalSerializer(approval, context={'request': request})
            return Response(
                {
                    "message": "Coach approved successfully",
                    "approval": serializer.data
                },
                status=status.HTTP_200_OK
            )
        except CoachApproval.DoesNotExist:
            return Response(
                {"error": "Coach not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class RejectCoachView(APIView):
    """
    API endpoint for admins to reject a coach
    POST /api/admin/coaches/<id>/reject/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        if not is_admin(request.user):
            return Response(
                {"error": "Only admins can reject coaches"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        rejection_reason = request.data.get('rejection_reason', '').strip()
        
        # Validate rejection reason
        if not rejection_reason:
            return Response(
                {"error": "Rejection reason is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(rejection_reason) < 20:
            return Response(
                {"error": "Rejection reason must be at least 20 characters"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            approval = CoachApproval.objects.get(coach_id=pk)
            
            # Update approval status
            approval.status = 'rejected'
            approval.rejection_reason = rejection_reason
            approval.reviewed_by = request.user
            approval.reviewed_at = timezone.now()
            approval.save()
            
            # Remove admin notifications for this coach
            AdminNotification.objects.filter(coach=approval.coach).delete()
            
            # TODO: Send rejection email (will implement in task 7)
            
            serializer = CoachApprovalSerializer(approval, context={'request': request})
            return Response(
                {
                    "message": "Coach rejected successfully",
                    "approval": serializer.data
                },
                status=status.HTTP_200_OK
            )
        except CoachApproval.DoesNotExist:
            return Response(
                {"error": "Coach not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class AdminNotificationListView(APIView):
    """
    API endpoint for admins to view notifications
    GET /api/admin/notifications/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not is_admin(request.user):
            return Response(
                {"error": "Only admins can view notifications"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notifications = AdminNotification.objects.filter(is_read=False)
        serializer = AdminNotificationSerializer(notifications, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminNotificationMarkReadView(APIView):
    """
    API endpoint to mark notification as read
    PATCH /api/admin/notifications/<id>/read/
    """
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, pk):
        if not is_admin(request.user):
            return Response(
                {"error": "Only admins can mark notifications as read"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            notification = AdminNotification.objects.get(pk=pk)
            notification.is_read = True
            notification.save()
            
            serializer = AdminNotificationSerializer(notification, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except AdminNotification.DoesNotExist:
            return Response(
                {"error": "Notification not found"},
                status=status.HTTP_404_NOT_FOUND
            )
