from django.urls import path, include
from . import views
from .admin_views import AdminUserViewSet

urlpatterns = [
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
    
    # Performance endpoints
    path("", include("performance.urls")),
]
