from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .activity_models import UserActivity
from .models import User


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def activity_feed(request):
    """Get activity feed with filters"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    # Filters
    action_type = request.GET.get('action_type')
    user_id = request.GET.get('user_id')
    days = int(request.GET.get('days', 30))
    limit = int(request.GET.get('limit', 50))
    
    # Base query
    activities = UserActivity.objects.select_related('user').all()
    
    # Apply filters
    if action_type:
        activities = activities.filter(action_type=action_type)
    if user_id:
        activities = activities.filter(user_id=user_id)
    if days:
        since = timezone.now() - timedelta(days=days)
        activities = activities.filter(created_at__gte=since)
    
    # Limit results
    activities = activities[:limit]
    
    # Format response
    data = []
    for activity in activities:
        data.append({
            'id': activity.id,
            'user': {
                'id': activity.user.id,
                'username': activity.user.username,
                'full_name': activity.user.get_full_name(),
                'role': activity.user.role,
            },
            'action_type': activity.action_type,
            'action_label': activity.get_action_type_display(),
            'description': activity.description,
            'metadata': activity.metadata,
            'created_at': activity.created_at.isoformat(),
        })
    
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def activity_stats(request):
    """Get activity statistics"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    days = int(request.GET.get('days', 7))
    since = timezone.now() - timedelta(days=days)
    
    # Total activities
    total = UserActivity.objects.filter(created_at__gte=since).count()
    
    # By action type
    by_type = UserActivity.objects.filter(created_at__gte=since).values('action_type').annotate(count=Count('id')).order_by('-count')
    
    # Most active users
    most_active = UserActivity.objects.filter(created_at__gte=since).values('user__username', 'user__role').annotate(count=Count('id')).order_by('-count')[:10]
    
    # Recent goals
    goals_created = UserActivity.objects.filter(action_type='goal_created', created_at__gte=since).count()
    goals_completed = UserActivity.objects.filter(action_type='goal_completed', created_at__gte=since).count()
    
    # Recent workouts
    workouts_logged = UserActivity.objects.filter(action_type='workout_logged', created_at__gte=since).count()
    
    return Response({
        'total_activities': total,
        'by_type': list(by_type),
        'most_active_users': list(most_active),
        'goals_created': goals_created,
        'goals_completed': goals_completed,
        'workouts_logged': workouts_logged,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_activity_timeline(request, user_id):
    """Get activity timeline for specific user"""
    if request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    limit = int(request.GET.get('limit', 100))
    activities = UserActivity.objects.filter(user=user).select_related('user')[:limit]
    
    data = []
    for activity in activities:
        data.append({
            'id': activity.id,
            'action_type': activity.action_type,
            'action_label': activity.get_action_type_display(),
            'description': activity.description,
            'metadata': activity.metadata,
            'created_at': activity.created_at.isoformat(),
        })
    
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name(),
            'role': user.role,
        },
        'activities': data
    })
