from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import (
    register_api, 
    login_api,
    CoachCredentialUploadView,
    CoachCredentialListView,
    CoachCredentialDeleteView,
    CoachStatusView
)
from .password_reset_views import request_password_reset, reset_password
from .coach_request_views import (
    AvailableCoachesView,
    CoachRequestViewSet,
    CoachCapacityView,
    CoachPauseRequestsView,
    CoachResumeRequestsView,
    MyAthletesView,
    MyCoachesView
)
from .coach_dashboard_views import CoachDashboardStatsView

router = SimpleRouter()
router.register(r'coach-requests', CoachRequestViewSet, basename='coach-request')

urlpatterns = [
    path("register/", register_api, name="register_api"),
    path("login/", login_api, name="login_api"),
    path("password-reset/request/", request_password_reset, name="password_reset_request"),
    path("password-reset/confirm/", reset_password, name="password_reset_confirm"),
    path("coach/credentials/", CoachCredentialUploadView.as_view(), name="coach_credential_upload"),
    path("coach/credentials/list/", CoachCredentialListView.as_view(), name="coach_credential_list"),
    path("coach/credentials/<int:pk>/", CoachCredentialDeleteView.as_view(), name="coach_credential_delete"),
    path("coach/status/", CoachStatusView.as_view(), name="coach_status"),
    
    # Coach request system
    path("coaches/available/", AvailableCoachesView.as_view(), name="available_coaches"),
    path("coaches/capacity-status/", CoachCapacityView.as_view(), name="coach_capacity_status"),
    path("coaches/pause-requests/", CoachPauseRequestsView.as_view(), name="coach_pause_requests"),
    path("coaches/resume-requests/", CoachResumeRequestsView.as_view(), name="coach_resume_requests"),
    path("coaches/my-athletes/", MyAthletesView.as_view(), name="my_athletes"),
    path("coaches/dashboard-stats/", CoachDashboardStatsView.as_view(), name="coach_dashboard_stats"),
    
    # Athlete endpoints
    path("athlete/my-coaches/", MyCoachesView.as_view(), name="my_coaches"),
] + router.urls
