"""
Training Effectiveness Score (TES) API Views
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model

from performance.tes_calculator import TESCalculator

User = get_user_model()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def athlete_tes_analysis(request, athlete_id):
    """
    Get comprehensive TES analysis for a specific athlete
    
    GET /api/performance/tes/athlete/<athlete_id>/
    
    Only accessible by:
    - Coaches assigned to this athlete
    - Admins
    - The athlete themselves
    """
    try:
        athlete = User.objects.get(id=athlete_id, role='athlete')
    except User.DoesNotExist:
        return Response(
            {'error': 'Athlete not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check permissions
    if request.user.role == 'athlete':
        # Athletes can only view their own TES
        if request.user.id != athlete_id:
            return Response(
                {'error': 'You can only view your own training analysis'},
                status=status.HTTP_403_FORBIDDEN
            )
    elif request.user.role == 'coach':
        # Coaches can only view their assigned athletes
        from accounts.models import CoachAthleteAssignment
        is_assigned = CoachAthleteAssignment.objects.filter(
            coach=request.user,
            athlete=athlete,
            is_active=True
        ).exists()
        
        if not is_assigned:
            return Response(
                {'error': 'You are not assigned to this athlete'},
                status=status.HTTP_403_FORBIDDEN
            )
    elif request.user.role != 'admin':
        return Response(
            {'error': 'Insufficient permissions'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Calculate TES
    tes_data = TESCalculator.calculate_tes(athlete)
    
    # Add athlete info
    tes_data['athlete'] = {
        'id': athlete.id,
        'name': athlete.get_full_name(),
        'username': athlete.username
    }
    
    return Response(tes_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_athletes_tes_summary(request):
    """
    Get TES summary for all athletes assigned to this coach
    
    GET /api/performance/tes/my-athletes/
    
    Returns list of athletes with their TES scores
    """
    if request.user.role != 'coach':
        return Response(
            {'error': 'Only coaches can access this endpoint'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    from accounts.models import CoachAthleteAssignment
    
    # Get all active assignments
    assignments = CoachAthleteAssignment.objects.filter(
        coach=request.user,
        is_active=True
    ).select_related('athlete')
    
    athletes_tes = []
    for assignment in assignments:
        athlete = assignment.athlete
        tes_data = TESCalculator.calculate_tes(athlete)
        
        athletes_tes.append({
            'athlete_id': athlete.id,
            'athlete_name': athlete.get_full_name(),
            'athlete_username': athlete.username,
            'overall_score': tes_data['overall_score'],
            'status': tes_data['status'],
            'consistency_score': tes_data['consistency']['score'],
            'recovery_score': tes_data['recovery']['score'],
            'goal_progress_score': tes_data['goal_progress']['score'],
            'needs_attention': tes_data['overall_score'] < 70,
            'critical': tes_data['overall_score'] < 60
        })
    
    # Sort by score (lowest first - needs most attention)
    athletes_tes.sort(key=lambda x: x['overall_score'])
    
    return Response({
        'total_athletes': len(athletes_tes),
        'needs_attention': sum(1 for a in athletes_tes if a['needs_attention']),
        'critical': sum(1 for a in athletes_tes if a['critical']),
        'athletes': athletes_tes
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_tes_analysis(request):
    """
    Get TES analysis for the authenticated athlete
    
    GET /api/performance/tes/my-analysis/
    """
    if request.user.role != 'athlete':
        return Response(
            {'error': 'Only athletes can access this endpoint'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    tes_data = TESCalculator.calculate_tes(request.user)
    
    return Response(tes_data)
