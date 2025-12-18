from django.contrib import admin
from django.urls import path, include
from .view import home  

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("api/accounts/", include("accounts.urls")),
]
