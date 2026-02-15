from django.urls import path, include
from . import views
from .admin_views import (
    AdminUserViewSet,
    PendingCoachesListView,
    CoachDetailView,
    ApproveCoachView,
    RejectCoachView,
    AdminNotificationListView,
    AdminNotificationMarkReadView,
    AdminActivityTypeListView,
    AdminActivityTypeDetailView,
    AdminCoachAthleteAssignmentListView,
    AdminCoachAthleteAssignmentDetailView,
    CoachAssignedAthletesView,
    AthleteAssignedCoachesView,
    AdminDebugCoachStatusView,
    AdminBenchmarkListView,
    AdminBenchmarkDetailView
)
from .coach_views import (
    upload_credential,
    list_credentials,
    delete_credential,
    coach_status
)

urlpatterns = [
    # CSRF token
    path("csrf/", views.get_csrf, name="get-csrf"),
    
    # Auth endpoints
    path("auth/register/", views.register_api, name="register"),
    path("auth/login/", views.login_api, name="login"),
    path("auth/me/", views.current_user, name="current-user"),
    path("auth/set-my-role/", views.set_my_role, name="set-my-role"),
    path("auth/set-role/", views.set_role, name="set-role"),  # Admin only
    
    # Coach credential endpoints
    path("auth/coach/credentials/", upload_credential, name="coach-upload-credential"),
    path("auth/coach/credentials/list/", list_credentials, name="coach-list-credentials"),
    path("auth/coach/credentials/<int:credential_id>/", delete_credential, name="coach-delete-credential"),
    path("auth/coach/status/", coach_status, name="coach-status"),
    
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
    
    # Admin activity types (exercises/workouts)
    path("admin/activity-types/", AdminActivityTypeListView.as_view(), name='admin-activity-types'),
    path("admin/activity-types/<int:pk>/", AdminActivityTypeDetailView.as_view(), name='admin-activity-type-detail'),
    
    # Admin coach-athlete assignments
    path("admin/assignments/", AdminCoachAthleteAssignmentListView.as_view(), name='admin-assignments'),
    path("admin/assignments/<int:pk>/", AdminCoachAthleteAssignmentDetailView.as_view(), name='admin-assignment-detail'),
    
    # Coach endpoints
    path("coach/athletes/", CoachAssignedAthletesView.as_view(), name='coach-athletes'),
    
    # Athlete endpoints
    path("athlete/coaches/", AthleteAssignedCoachesView.as_view(), name='athlete-coaches'),
    
    # Debug endpoints (admin only)
    path("admin/debug/coach-status/", AdminDebugCoachStatusView.as_view(), name='admin-debug-coach-status'),
    
    # Performance endpoints
    path("", include("performance.urls")),
]
