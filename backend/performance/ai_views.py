"""
API Views for AI-powered suggestions
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .ai_models import SuggestedGoal, SuggestedWorkout
from .ai_service import AIService
from .serializers import SuggestedGoalSerializer, SuggestedWorkoutSerializer


class AIGoalSuggestionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for AI-generated goal suggestions"""
    
    serializer_class = SuggestedGoalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return suggestions for current user"""
        return SuggestedGoal.objects.filter(
            athlete=self.request.user
        ).order_by('-suggested_at')
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate new goal suggestions"""
        try:
            # Delete old pending suggestions
            SuggestedGoal.objects.filter(
                athlete=request.user,
                status='pending'
            ).delete()
            
            # Generate new suggestions
            suggestions = AIService.generate_goal_suggestions(request.user)
            
            serializer = self.get_serializer(suggestions, many=True)
            return Response({
                'success': True,
                'suggestions': serializer.data,
                'message': 'Generated 3 personalized goal suggestions'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a goal suggestion"""
        suggestion = self.get_object()
        
        if suggestion.status != 'pending':
            return Response({
                'success': False,
                'error': 'This suggestion has already been responded to'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        goal = suggestion.accept()
        
        if goal:
            return Response({
                'success': True,
                'message': 'Goal accepted and added to your goals',
                'goal_id': goal.id
            })
        else:
            return Response({
                'success': False,
                'error': 'Failed to create goal'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a goal suggestion"""
        suggestion = self.get_object()
        
        if suggestion.status != 'pending':
            return Response({
                'success': False,
                'error': 'This suggestion has already been responded to'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        suggestion.reject()
        
        return Response({
            'success': True,
            'message': 'Goal suggestion rejected'
        })
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending suggestions"""
        suggestions = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(suggestions, many=True)
        return Response(serializer.data)


class AIWorkoutSuggestionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for AI-generated workout suggestions"""
    
    serializer_class = SuggestedWorkoutSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return suggestions for current user"""
        return SuggestedWorkout.objects.filter(
            athlete=self.request.user
        ).order_by('-suggested_at')
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate new workout suggestions"""
        try:
            # Delete old suggested workouts
            SuggestedWorkout.objects.filter(
                athlete=request.user,
                status='suggested'
            ).delete()
            
            # Generate new suggestions
            suggestions = AIService.generate_workout_suggestions(request.user)
            
            serializer = self.get_serializer(suggestions, many=True)
            return Response({
                'success': True,
                'suggestions': serializer.data,
                'message': 'Generated 3 personalized workout suggestions'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def add_to_plan(self, request, pk=None):
        """Add workout to training plan"""
        suggestion = self.get_object()
        
        if suggestion.status != 'suggested':
            return Response({
                'success': False,
                'error': 'This workout has already been processed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        suggestion.add_to_plan()
        
        return Response({
            'success': True,
            'message': 'Workout added to your training plan'
        })
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """Dismiss a workout suggestion"""
        suggestion = self.get_object()
        
        if suggestion.status not in ['suggested', 'added_to_plan']:
            return Response({
                'success': False,
                'error': 'This workout cannot be dismissed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        suggestion.dismiss()
        
        return Response({
            'success': True,
            'message': 'Workout suggestion dismissed'
        })
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active workout suggestions (suggested or added to plan)"""
        suggestions = self.get_queryset().filter(
            status__in=['suggested', 'added_to_plan']
        )
        serializer = self.get_serializer(suggestions, many=True)
        return Response(serializer.data)
