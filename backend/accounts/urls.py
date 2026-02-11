from django.urls import path
from .views import (
    register_api, 
    login_api,
    CoachCredentialUploadView,
    CoachCredentialListView,
    CoachCredentialDeleteView,
    CoachStatusView
)

urlpatterns = [
    path("register/", register_api, name="register_api"),
    path("login/", login_api, name="login_api"),
    path("coach/credentials/", CoachCredentialUploadView.as_view(), name="coach_credential_upload"),
    path("coach/credentials/list/", CoachCredentialListView.as_view(), name="coach_credential_list"),
    path("coach/credentials/<int:pk>/", CoachCredentialDeleteView.as_view(), name="coach_credential_delete"),
    path("coach/status/", CoachStatusView.as_view(), name="coach_status"),
]
