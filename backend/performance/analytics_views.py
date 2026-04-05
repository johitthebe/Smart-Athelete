from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Avg, Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from .models import PerformanceLog, Goal
from django.contrib.auth import get_user_model

User = get_user_model()


class DetailedAnalyticsView(APIView):
    """
    Provides detailed analytics with period comparisons
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        period = request.query_params.get('period', 'month')  # week, month, quarter, year
        
        # Calculate date ranges
        now = timezone.now()
        period_days = {
            'week': 7,
            'month': 30,
            'quarter': 90,
            'year': 365
        }
        
        days = period_days.get(period, 30)
        current_start = now - timedelta(days=days)
        previous_start = now - timedelta(days=days * 2)
        previous_end = current_start
        
        # Get logs for both periods
        current_logs = PerformanceLog.objects.filter(
            athlete=user,
            date__gte=current_start,
            date__lte=now
        )
        
        previous_logs = PerformanceLog.objects.filter(
            athlete=user,
            date__gte=previous_start,
            date__lt=previous_end
        )
        
        # Calculate current period stats
        current_stats = current_logs.aggregate(
            total_sessions=Count('id'),
            total_distance=Sum('distance'),
            total_duration=Sum('duration'),
            total_calories=Sum('calories'),
            avg_intensity=Avg('intensity'),
            avg_distance=Avg('distance'),
            avg_duration=Avg('duration'),
            avg_calories=Avg('calories')
        )
        
        # Calculate previous period stats
        previous_stats = previous_logs.aggregate(
            total_sessions=Count('id'),
            total_distance=Sum('distance'),
            total_duration=Sum('duration'),
            total_calories=Sum('calories'),
            avg_intensity=Avg('intensity'),
            avg_distance=Avg('distance'),
            avg_duration=Avg('duration'),
            avg_calories=Avg('calories')
        )
        
        # Calculate improvements
        def calculate_improvement(current, previous):
            if previous is None or previous == 0:
                return 100 if current and current > 0 else 0
            if current is None:
                return -100
            return ((current - previous) / previous) * 100
        
        improvements = {
            'sessions': calculate_improvement(
                current_stats['total_sessions'],
                previous_stats['total_sessions']
            ),
            'distance': calculate_improvement(
                current_stats['total_distance'],
                previous_stats['total_distance']
            ),
            'duration': calculate_improvement(
                current_stats['total_duration'],
                previous_stats['total_duration']
            ),
            'calories': calculate_improvement(
                current_stats['total_calories'],
                previous_stats['total_calories']
            ),
            'intensity': calculate_improvement(
                current_stats['avg_intensity'],
                previous_stats['avg_intensity']
            ),
        }
        
        # Activity breakdown
        activity_breakdown = current_logs.values(
            'activity_type__name',
            'activity_type__icon'
        ).annotate(
            count=Count('id'),
            avg_intensity=Avg('intensity'),
            total_distance=Sum('distance'),
            total_duration=Sum('duration')
        ).order_by('-count')
        
        # Daily trend data
        daily_data = []
        for i in range(days):
            day = current_start + timedelta(days=i)
            day_logs = current_logs.filter(date__date=day.date())
            
            if day_logs.exists():
                day_stats = day_logs.aggregate(
                    distance=Sum('distance'),
                    duration=Sum('duration'),
                    calories=Sum('calories'),
                    avg_intensity=Avg('intensity'),
                    sessions=Count('id')
                )
                daily_data.append({
                    'date': day.date().isoformat(),
                    'distance': float(day_stats['distance'] or 0),
                    'duration': float(day_stats['duration'] or 0),
                    'calories': float(day_stats['calories'] or 0),
                    'intensity': float(day_stats['avg_intensity'] or 0),
                    'sessions': day_stats['sessions']
                })
        
        # Weekly comparison
        weeks_data = []
        for week_num in range(4):
            week_start = current_start + timedelta(days=week_num * 7)
            week_end = week_start + timedelta(days=7)
            week_logs = current_logs.filter(date__gte=week_start, date__lt=week_end)
            
            week_stats = week_logs.aggregate(
                sessions=Count('id'),
                distance=Sum('distance'),
                duration=Sum('duration'),
                avg_intensity=Avg('intensity')
            )
            
            weeks_data.append({
                'week': week_num + 1,
                'sessions': week_stats['sessions'] or 0,
                'distance': float(week_stats['distance'] or 0),
                'duration': float(week_stats['duration'] or 0),
                'avg_intensity': float(week_stats['avg_intensity'] or 0)
            })
        
        # Personal records
        personal_records = {
            'longest_distance': current_logs.order_by('-distance').first(),
            'longest_duration': current_logs.order_by('-duration').first(),
            'highest_intensity': current_logs.order_by('-intensity').first(),
            'most_calories': current_logs.order_by('-calories').first(),
        }
        
        pr_data = {}
        for key, log in personal_records.items():
            if log:
                pr_data[key] = {
                    'value': getattr(log, key.split('_')[1] if '_' in key else 'value'),
                    'date': log.date.isoformat(),
                    'activity': log.activity_type.name if log.activity_type else log.event
                }
        
        # Goal progress
        active_goals = Goal.objects.filter(
            athlete=user,
            status='active'
        )
        
        goal_progress = []
        for goal in active_goals:
            progress = goal.progress_percentage()
            goal_progress.append({
                'id': goal.id,
                'name': goal.name,
                'progress': round(progress, 2),
                'target_value': float(goal.target_value),
                'current_value': float(goal.current_value),
                'unit': goal.target_unit,
                'deadline': goal.deadline.isoformat() if goal.deadline else None
            })
        
        # Consistency score (percentage of days with activity)
        days_with_activity = current_logs.values('date__date').distinct().count()
        consistency_score = (days_with_activity / days) * 100
        
        return Response({
            'period': period,
            'current_period': {
                'start': current_start.date().isoformat(),
                'end': now.date().isoformat(),
                'stats': {
                    'total_sessions': current_stats['total_sessions'] or 0,
                    'total_distance': float(current_stats['total_distance'] or 0),
                    'total_duration': float(current_stats['total_duration'] or 0),
                    'total_calories': float(current_stats['total_calories'] or 0),
                    'avg_intensity': float(current_stats['avg_intensity'] or 0),
                    'avg_distance': float(current_stats['avg_distance'] or 0),
                    'avg_duration': float(current_stats['avg_duration'] or 0),
                    'avg_calories': float(current_stats['avg_calories'] or 0),
                }
            },
            'previous_period': {
                'start': previous_start.date().isoformat(),
                'end': previous_end.date().isoformat(),
                'stats': {
                    'total_sessions': previous_stats['total_sessions'] or 0,
                    'total_distance': float(previous_stats['total_distance'] or 0),
                    'total_duration': float(previous_stats['total_duration'] or 0),
                    'total_calories': float(previous_stats['total_calories'] or 0),
                    'avg_intensity': float(previous_stats['avg_intensity'] or 0),
                    'avg_distance': float(previous_stats['avg_distance'] or 0),
                    'avg_duration': float(previous_stats['avg_duration'] or 0),
                    'avg_calories': float(previous_stats['avg_calories'] or 0),
                }
            },
            'improvements': improvements,
            'activity_breakdown': list(activity_breakdown),
            'daily_trend': daily_data,
            'weekly_comparison': weeks_data,
            'personal_records': pr_data,
            'goal_progress': goal_progress,
            'consistency_score': round(consistency_score, 2),
            'days_with_activity': days_with_activity,
            'total_days': days
        })
