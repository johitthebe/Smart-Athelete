from django.urls import path
from .views import get_csrf, register_api, login_api, set_role

urlpatterns = [
    path("csrf/", get_csrf, name="get_csrf"),
    path("register/", register_api, name="register_api"),
    path("login/", login_api, name="login_api"),
    path("set-role/", set_role, name="set_role"),
]
