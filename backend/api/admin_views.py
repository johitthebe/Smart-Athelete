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
