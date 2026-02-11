from django.urls import path, include
from . import views
from .admin_views import (
    AdminUserViewSet,
    PendingCoachesListView,
    CoachDetailView,
    ApproveCoachView,
    RejectCoachView,
    AdminNotificationListView,
    AdminNotificationMarkReadView
)

# Quick fix endpoint to set admin role
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model

User = get_user_model()

@api_view(["POST"])
@permission_classes([AllowAny])
def quick_set_admin(request):
    """Temporary endpoint to set a user as admin - REMOVE IN PRODUCTION"""
    username = request.data.get("username")
    password = request.data.get("password")
    
    if not username or not password:
        return Response({"error": "Username and password required"}, status=400)
    
    try:
        user = User.objects.get(username=username)
        # Verify password
        if user.check_password(password):
            user.role = 'admin'
            user.save()
            return Response({
                "message": f"User {username} is now an admin!",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "role": user.role
                }
            })
        else:
            return Response({"error": "Invalid password"}, status=401)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=404)

urlpatterns = [
    # TEMPORARY - Quick fix to set admin role
    path("quick-set-admin/", quick_set_admin, name="quick-set-admin"),
    
    # CSRF token
    path("csrf/", views.get_csrf, name="get-csrf"),
    
    # Auth endpoints
    path("auth/register/", views.register_api, name="register"),
    path("auth/login/", views.login_api, name="login"),
    path("auth/me/", views.current_user, name="current-user"),
    path("auth/set-my-role/", views.set_my_role, name="set-my-role"),
    path("auth/set-role/", views.set_role, name="set-role"),  # Admin only
    
    # Admin user management (manual routes to avoid router conflict)
    path("admin/users/", AdminUserViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='admin-users-list'),
    path("admin/users/stats/", AdminUserViewSet.as_view({
        'get': 'stats'
    }), name='admin-users-stats'),
    path("admin/users/<int:pk>/", AdminUserViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='admin-users-detail'),
    path("admin/users/<int:pk>/change_role/", AdminUserViewSet.as_view({
        'post': 'change_role'
    }), name='admin-users-change-role'),
    path("admin/users/<int:pk>/toggle_active/", AdminUserViewSet.as_view({
        'post': 'toggle_active'
    }), name='admin-users-toggle-active'),
    
    # Admin coach approval endpoints
    path("admin/coaches/pending/", PendingCoachesListView.as_view(), name='admin-coaches-pending'),
    path("admin/coaches/<int:pk>/", CoachDetailView.as_view(), name='admin-coach-detail'),
    path("admin/coaches/<int:pk>/approve/", ApproveCoachView.as_view(), name='admin-coach-approve'),
    path("admin/coaches/<int:pk>/reject/", RejectCoachView.as_view(), name='admin-coach-reject'),
    
    # Admin notifications
    path("admin/notifications/", AdminNotificationListView.as_view(), name='admin-notifications'),
    path("admin/notifications/<int:pk>/read/", AdminNotificationMarkReadView.as_view(), name='admin-notification-read'),
    
    # Performance endpoints
    path("", include("performance.urls")),
]
