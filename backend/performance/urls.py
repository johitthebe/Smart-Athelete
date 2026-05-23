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
from .analytics_views import DetailedAnalyticsView
from .tes_views import athlete_tes_analysis, my_athletes_tes_summary, my_tes_analysis

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
    path('detailed-analytics/', DetailedAnalyticsView.as_view(), name='detailed-analytics'),
    
    # Training Effectiveness Score (TES) endpoints
    path('tes/athlete/<int:athlete_id>/', athlete_tes_analysis, name='athlete-tes-analysis'),
    path('tes/my-athletes/', my_athletes_tes_summary, name='my-athletes-tes-summary'),
    path('tes/my-analysis/', my_tes_analysis, name='my-tes-analysis'),
] + router.urls

