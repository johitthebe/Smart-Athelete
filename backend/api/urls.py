from django.urls import path
from . import views

urlpatterns = [
    path('csrf/', views.get_csrf, name='get_csrf'),
    path('register/', views.register_api, name='register'),
    path('login/', views.login_api, name='login'),
    path('set-role/', views.set_role, name='set_role'),
]
