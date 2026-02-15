from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Goal, Benchmark, PerformanceLog, ActivityType
from .serializers import (
    GoalSerializer,
    BenchmarkSerializer,
    PerformanceLogSerializer,
    ActivityTypeSerializer,
)

User = get_user_model()


def is_super_admin(user):
    return getattr(user, "role", None) == "admin" or user.is_superuser


class ActivityTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for activity types"""
    queryset = ActivityType.objects.all()
    serializer_class = ActivityTypeSerializer
    permission_classes = [permissions.IsAuthenticated]


class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only goals for the authenticated athlete"""
        return Goal.objects.filter(athlete=self.request.user).prefetch_related('logs')

    @action(detail=False, methods=["get"])
    def active(self, request):
        """Get all active goals"""
        goals = self.get_queryset().filter(status="active")
        serializer = self.get_serializer(goals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def completed(self, request):
        """Get all completed goals"""
        goals = self.get_queryset().filter(status="completed")
        serializer = self.get_serializer(goals, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=["get"])
    def check_active(self, request):
        """Check if athlete has any active goals"""
        has_active_goals = self.get_queryset().filter(status="active").exists()
        return Response({
            'has_active_goals': has_active_goals,
            'message': 'You have active goals' if has_active_goals else 'Create a goal first to start logging performance'
        })

    @action(detail=True, methods=["post"])
    def mark_completed(self, request, pk=None):
        """Mark a goal as completed"""
        goal = self.get_object()
        goal.status = "completed"
        goal.save()
        serializer = self.get_serializer(goal)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Delete goal with cascade confirmation"""
        goal = self.get_object()
        log_count = goal.logs.count()
        
        # Return confirmation info
        if request.query_params.get('confirm') != 'true':
            return Response({
                'message': f'This will delete the goal and {log_count} associated performance log(s). Add ?confirm=true to proceed.',
                'log_count': log_count
            }, status=status.HTTP_200_OK)
        
        # Proceed with deletion
        return super().destroy(request, *args, **kwargs)


class BenchmarkViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Benchmark.objects.all()
    serializer_class = BenchmarkSerializer
    permission_classes = [permissions.IsAuthenticated]


class PerformanceLogViewSet(viewsets.ModelViewSet):
    serializer_class = PerformanceLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only logs for the authenticated athlete"""
        queryset = PerformanceLog.objects.filter(
            athlete=self.request.user
        ).select_related('goal', 'activity_type').order_by("-date", "-created_at")
        
        # Filter by goal
        goal_id = self.request.query_params.get('goal')
        if goal_id:
            queryset = queryset.filter(goal_id=goal_id)
        
        # Filter by activity type
        activity_type_id = self.request.query_params.get('activity_type')
        if activity_type_id:
            queryset = queryset.filter(activity_type_id=activity_type_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create performance log with goal requirement check"""
        # Check if athlete has active goals
        has_active_goals = Goal.objects.filter(
            athlete=request.user,
            status='active'
        ).exists()
        
        if not has_active_goals:
            return Response({
                'error': 'You must create an active goal before logging performance',
                'message': 'Create a goal first to start tracking your progress'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def by_event(self, request):
        """Get logs by event (legacy)"""
        event = request.query_params.get("event")
        if event:
            logs = self.get_queryset().filter(event=event)
            serializer = self.get_serializer(logs, many=True)
            return Response(serializer.data)
        return Response(
            {"error": "event parameter required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    
    @action(detail=False, methods=["get"])
    def aggregated_metrics(self, request):
        """Get aggregated metrics for a goal"""
        goal_id = request.query_params.get('goal')
        if not goal_id:
            return Response(
                {"error": "goal parameter required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        logs = self.get_queryset().filter(goal_id=goal_id)
        
        from django.db.models import Sum, Avg, Count
        aggregates = logs.aggregate(
            total_distance=Sum('distance'),
            total_duration=Sum('duration'),
            total_calories=Sum('calories'),
            avg_heart_rate=Avg('heart_rate'),
            avg_pace=Avg('pace'),
            log_count=Count('id')
        )
        
        return Response(aggregates)


class AdminStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not is_super_admin(request.user):
            return Response(
                {"detail": "Forbidden"},
                status=status.HTTP_403_FORBIDDEN,
            )

        total_athletes = User.objects.filter(role="athlete").count()
        total_coaches = User.objects.filter(role="coach").count()
        active_goals = Goal.objects.filter(status="active").count()
        total_logs = PerformanceLog.objects.count()

        return Response(
            {
                "total_athletes": total_athletes,
                "total_coaches": total_coaches,
                "active_goals": active_goals,
                "total_logs": total_logs,
            }
        )

