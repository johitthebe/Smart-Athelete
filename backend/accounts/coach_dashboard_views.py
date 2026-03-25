from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import User, CoachAthleteAssignment
from .coach_request_models import CoachRequest


class CoachDashboardStatsView(APIView):
    """
    GET /api/auth/coaches/dashboard-stats/
    Returns dashboard statistics for coach
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if request.user.role != 'coach':
            return Response(
                {"error": "Only coaches can access dashboard stats"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Total athletes
        total_athletes = CoachAthleteAssignment.objects.filter(
            coach=request.user,
            is_active=True
        ).count()
        
        # Pending requests
        pending_requests = CoachRequest.objects.filter(
            coach=request.user,
            status='pending'
        ).count()
        
        # Active goals (from all assigned athletes)
        from performance.models import Goal
        active_goals = Goal.objects.filter(
            athlete__assigned_coaches__coach=request.user,
            athlete__assigned_coaches__is_active=True,
            status='active'
        ).count()
        
        # Recent activity (last 5 activities from athletes)
        from performance.models import PerformanceLog
        recent_logs = PerformanceLog.objects.filter(
            athlete__assigned_coaches__coach=request.user,
            athlete__assigned_coaches__is_active=True
        ).select_related('athlete', 'activity_type').order_by('-date')[:5]
        
        recent_activity = []
        for log in recent_logs:
            recent_activity.append({
                'athlete_name': log.athlete.get_full_name() or log.athlete.username,
                'activity': log.activity_type.name if log.activity_type else 'Workout',
                'distance': float(log.distance) if log.distance else None,
                'duration': log.duration,
                'date': log.date.isoformat(),
                'intensity': log.intensity_level if log.intensity_level else 'medium'
            })
        
        return Response({
            'total_athletes': total_athletes,
            'pending_requests': pending_requests,
            'active_goals': active_goals,
            'recent_activity': recent_activity
        })
