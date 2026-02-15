# performance/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GoalViewSet,
    BenchmarkViewSet,
    PerformanceLogViewSet,
    ActivityTypeViewSet,
    AdminStatsView
)

router = DefaultRouter()
router.register(r'goals', GoalViewSet, basename='goal')
router.register(r'benchmarks', BenchmarkViewSet, basename='benchmark')
router.register(r'performance-logs', PerformanceLogViewSet, basename='performance-log')
router.register(r'activity-types', ActivityTypeViewSet, basename='activity-type')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/stats/', AdminStatsView.as_view(), name='admin-stats'),
]

