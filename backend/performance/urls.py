# performance/urls.py
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import (
    GoalViewSet,
    BenchmarkViewSet,
    PerformanceLogViewSet,
    ActivityTypeViewSet,
    BenchmarkComparisonView,
    AdminStatsView,
    CoachFeedbackViewSet
)
from .ai_views import AIGoalSuggestionViewSet, AIWorkoutSuggestionViewSet
from .report_views import PerformanceReportViewSet, PerformanceAnalyticsView
from .message_views import MessageViewSet

router = SimpleRouter()
router.register(r'goals', GoalViewSet, basename='goal')
router.register(r'benchmarks', BenchmarkViewSet, basename='benchmark')
router.register(r'performance-logs', PerformanceLogViewSet, basename='performance-log')
router.register(r'activity-types', ActivityTypeViewSet, basename='activity-type')
router.register(r'feedback', CoachFeedbackViewSet, basename='feedback')
router.register(r'ai/goal-suggestions', AIGoalSuggestionViewSet, basename='ai-goal-suggestion')
router.register(r'ai/workout-suggestions', AIWorkoutSuggestionViewSet, basename='ai-workout-suggestion')
router.register(r'reports', PerformanceReportViewSet, basename='report')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    path('benchmark-comparison/', BenchmarkComparisonView.as_view(), name='benchmark-comparison'),
    path('admin/stats/', AdminStatsView.as_view(), name='admin-stats'),
    path('analytics/', PerformanceAnalyticsView.as_view(), name='performance-analytics'),
] + router.urls

