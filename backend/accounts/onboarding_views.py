"""
Onboarding views for athlete profile creation and status checking
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import IntegrityError

from accounts.models import AthleteProfile
from accounts.serializers import AthleteProfileSerializer
from accounts.activity_utils import log_activity


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_profile(request):
    """
    Create athlete profile from onboarding wizard
    
    POST /api/onboarding/profile/
    
    Request body: All profile fields from 5 steps
    Response: 201 Created with profile data and AI goal suggestions
    """
    # Check if user is an athlete
    if request.user.role != 'athlete':
        return Response(
            {'error': 'Only athletes can create onboarding profiles'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if profile already exists
    if AthleteProfile.objects.filter(user=request.user).exists():
        return Response(
            {'error': 'Profile already exists for this user'},
            status=status.HTTP_409_CONFLICT
        )
    
    # Validate and create profile
    serializer = AthleteProfileSerializer(data=request.data, context={'request': request})
    
    if not serializer.is_valid():
        print(f"Validation errors: {serializer.errors}")
        return Response(
            {'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        profile = serializer.save()
        
        # Log activity
        log_activity(
            user=request.user,
            action_type='onboarding_completed',
            description=f"{request.user.username} completed onboarding",
            metadata={
                'fitness_level': profile.fitness_level,
                'primary_goal': profile.primary_goal,
                'primary_sport': profile.primary_sport
            },
            request=request
        )
        
        # Generate AI goal suggestions
        from performance.ai_service import AIService
        try:
            goal_suggestions = AIService.generate_onboarding_goals(profile)
        except Exception as e:
            # If AI fails, use fallback goals
            print(f"AI goal generation failed: {e}")
            goal_suggestions = _generate_fallback_goals(profile)
        
        return Response({
            'success': True,
            'profile': AthleteProfileSerializer(profile).data,
            'goal_suggestions': goal_suggestions
        }, status=status.HTTP_201_CREATED)
        
    except IntegrityError:
        return Response(
            {'error': 'Profile already exists for this user'},
            status=status.HTTP_409_CONFLICT
        )
    except Exception as e:
        return Response(
            {'error': f'Failed to create profile: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def onboarding_status(request):
    """
    Check if user has completed onboarding
    
    GET /api/onboarding/status/
    
    Response: {completed: bool, profile_id: int|null}
    """
    try:
        profile = AthleteProfile.objects.get(user=request.user)
        return Response({
            'completed': True,
            'profile_id': profile.id
        })
    except AthleteProfile.DoesNotExist:
        return Response({
            'completed': False,
            'profile_id': None
        })


def _generate_fallback_goals(profile):
    """
    Generate fallback goals when AI service fails
    Uses heuristic algorithm based on profile data
    """
    # Map fitness levels to baseline values
    fitness_multipliers = {
        'beginner': 0.7,
        'intermediate': 1.0,
        'advanced': 1.3,
        'elite': 1.6
    }
    
    # Map goal timeframes to weeks
    timeframe_weeks = {
        '1_month': 4,
        '3_months': 12,
        '6_months': 24,
        '1_year': 52,
        'ongoing': 12  # Default to 12 weeks
    }
    
    multiplier = fitness_multipliers.get(profile.fitness_level, 1.0)
    weeks = timeframe_weeks.get(profile.goal_timeframe, 12)
    
    # Generate goals based on primary goal
    if profile.primary_goal == 'endurance':
        base_distance = 5.0  # km
        return [
            {
                'difficulty_level': 'conservative',
                'event': f'{profile.primary_sport} - Distance',
                'target_value': round(base_distance * multiplier * 0.8, 1),
                'unit': 'km',
                'deadline_weeks': weeks,
                'reasoning': f'Build endurance gradually with {profile.weekly_availability} days per week',
                'training_required': f'{profile.weekly_availability} sessions per week, focus on consistency',
                'key_tip': 'Start slow and increase distance by 10% each week'
            },
            {
                'difficulty_level': 'recommended',
                'event': f'{profile.primary_sport} - Distance',
                'target_value': round(base_distance * multiplier, 1),
                'unit': 'km',
                'deadline_weeks': weeks,
                'reasoning': f'Optimal challenge for {profile.fitness_level} level',
                'training_required': f'{profile.weekly_availability} sessions with one long session weekly',
                'key_tip': 'Include one interval session per week'
            },
            {
                'difficulty_level': 'ambitious',
                'event': f'{profile.primary_sport} - Distance',
                'target_value': round(base_distance * multiplier * 1.3, 1),
                'unit': 'km',
                'deadline_weeks': weeks,
                'reasoning': f'Stretch goal for motivated {profile.fitness_level} athletes',
                'training_required': f'{profile.weekly_availability + 1} sessions per week with structured training',
                'key_tip': 'Prioritize recovery and nutrition'
            }
        ]
    
    elif profile.primary_goal == 'strength':
        base_weight = 50.0  # kg
        return [
            {
                'difficulty_level': 'conservative',
                'event': 'Strength Training',
                'target_value': round(base_weight * multiplier * 0.8, 1),
                'unit': 'kg total lift',
                'deadline_weeks': weeks,
                'reasoning': f'Build strength foundation with {profile.weekly_availability} days per week',
                'training_required': f'{profile.weekly_availability} strength sessions, focus on form',
                'key_tip': 'Master proper form before adding weight'
            },
            {
                'difficulty_level': 'recommended',
                'event': 'Strength Training',
                'target_value': round(base_weight * multiplier, 1),
                'unit': 'kg total lift',
                'deadline_weeks': weeks,
                'reasoning': f'Balanced strength progression for {profile.fitness_level}',
                'training_required': f'{profile.weekly_availability} sessions with progressive overload',
                'key_tip': 'Increase weight by 2.5-5% when you can do 3 sets of 8 reps'
            },
            {
                'difficulty_level': 'ambitious',
                'event': 'Strength Training',
                'target_value': round(base_weight * multiplier * 1.3, 1),
                'unit': 'kg total lift',
                'deadline_weeks': weeks,
                'reasoning': f'Aggressive strength gains for dedicated athletes',
                'training_required': f'{profile.weekly_availability + 1} sessions with periodization',
                'key_tip': 'Ensure adequate protein intake (1.6-2.2g per kg bodyweight)'
            }
        ]
    
    else:  # General fitness or other goals
        return [
            {
                'difficulty_level': 'conservative',
                'event': f'{profile.primary_goal.replace("_", " ").title()}',
                'target_value': 80,
                'unit': '% improvement',
                'deadline_weeks': weeks,
                'reasoning': f'Steady progress with {profile.weekly_availability} days per week',
                'training_required': f'{profile.weekly_availability} sessions per week',
                'key_tip': 'Focus on consistency over intensity'
            },
            {
                'difficulty_level': 'recommended',
                'event': f'{profile.primary_goal.replace("_", " ").title()}',
                'target_value': 100,
                'unit': '% improvement',
                'deadline_weeks': weeks,
                'reasoning': f'Optimal progress for {profile.fitness_level} level',
                'training_required': f'{profile.weekly_availability} varied sessions per week',
                'key_tip': 'Mix different training modalities'
            },
            {
                'difficulty_level': 'ambitious',
                'event': f'{profile.primary_goal.replace("_", " ").title()}',
                'target_value': 130,
                'unit': '% improvement',
                'deadline_weeks': weeks,
                'reasoning': f'Challenging goal for motivated athletes',
                'training_required': f'{profile.weekly_availability + 1} sessions with structured plan',
                'key_tip': 'Track progress weekly and adjust as needed'
            }
        ]
