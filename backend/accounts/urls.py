from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import (
    register_api, 
    login_api,
    logout_api,
    me,
    CoachCredentialUploadView,
    CoachCredentialListView,
    CoachCredentialDeleteView,
    CoachStatusView,
    change_password
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
from .coach_detail_views import CoachDetailView, CoachReviewsView
from .onboarding_views import create_profile, onboarding_status
from .activity_views import activity_feed, activity_stats, user_activity_timeline

router = SimpleRouter()
router.register(r'coach-requests', CoachRequestViewSet, basename='coach-request')

urlpatterns = [
    path("register/", register_api, name="register_api"),
    path("login/", login_api, name="login_api"),
    path("logout/", logout_api, name="logout_api"),
    path("me/", me, name="me"),
    path("change-password/", change_password, name="change_password"),
    path("password-reset/request/", request_password_reset, name="password_reset_request"),
    path("password-reset/confirm/", reset_password, name="password_reset_confirm"),
    path("coach/credentials/", CoachCredentialUploadView.as_view(), name="coach_credential_upload"),
    path("coach/credentials/list/", CoachCredentialListView.as_view(), name="coach_credential_list"),
    path("coach/credentials/<int:pk>/", CoachCredentialDeleteView.as_view(), name="coach_credential_delete"),
    path("coach/status/", CoachStatusView.as_view(), name="coach_status"),
    
    # Coach request system
    path("coaches/available/", AvailableCoachesView.as_view(), name="available_coaches"),
    path("coaches/<int:coach_id>/", CoachDetailView.as_view(), name="coach_detail"),
    path("coaches/<int:coach_id>/reviews/", CoachReviewsView.as_view(), name="coach_reviews"),
    path("coaches/capacity-status/", CoachCapacityView.as_view(), name="coach_capacity_status"),
    path("coaches/pause-requests/", CoachPauseRequestsView.as_view(), name="coach_pause_requests"),
    path("coaches/resume-requests/", CoachResumeRequestsView.as_view(), name="coach_resume_requests"),
    path("coaches/my-athletes/", MyAthletesView.as_view(), name="my_athletes"),
    path("coaches/dashboard-stats/", CoachDashboardStatsView.as_view(), name="coach_dashboard_stats"),
    
    # Athlete endpoints
    path("athlete/my-coaches/", MyCoachesView.as_view(), name="my_coaches"),
    
    # Onboarding endpoints
    path("onboarding/profile/", create_profile, name="onboarding_create_profile"),
    path("onboarding/status/", onboarding_status, name="onboarding_status"),
    
    # Activity tracking endpoints
    path("activities/feed/", activity_feed, name="activity_feed"),
    path("activities/stats/", activity_stats, name="activity_stats"),
    path("activities/user/<int:user_id>/", user_activity_timeline, name="user_activity_timeline"),
] + router.urls
