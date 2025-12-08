from django.urls import path
from . import views   # <-- this line was missing

urlpatterns = [
    path("csrf/", views.get_csrf, name="get-csrf"),
    path("register/", views.register_api, name="register"),
    path("login/", views.login_api, name="login"),
    path("set-role/", views.set_role, name="set-role"),
    path("user/", views.current_user, name="current-user"),  # current user (incl. Google)
]
