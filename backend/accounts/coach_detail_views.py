from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from django.db.models import Count
from .models import User, CoachAthleteAssignment


class CoachDetailView(APIView):
    """
    GET /api/auth/coaches/<id>/
    Returns detailed coach profile for preview
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, coach_id):
        coach = get_object_or_404(User, id=coach_id, role='coach')
        
        # Count current athletes
        current_athletes = CoachAthleteAssignment.objects.filter(
            coach=coach,
            is_active=True
        ).count()
        
        # Calculate available spots
        available_spots = 0
        if coach.max_athletes:
            available_spots = max(0, coach.max_athletes - current_athletes)
        
        data = {
            'id': coach.id,
            'coach_name': coach.get_full_name() or coach.username,
            'email': coach.email,
            'bio': getattr(coach, 'bio', ''),
            'specializations': [],  # Add if you have this field
            'accepting_requests': coach.accepting_requests,
            'available_spots': available_spots,
            'rating': 4.8,  # Placeholder - implement reviews system
            'total_reviews': 0,  # Placeholder
            'location': getattr(coach, 'location', 'Location not specified'),
            'certifications': [],  # Add if you have this field
            'total_athletes_coached': current_athletes,  # Simplified
            'current_active_athletes': current_athletes,
            'avg_improvement': 'N/A',  # Placeholder
            'availability': getattr(coach, 'availability', ''),
            'success_stories': [],  # Add if you have this field
        }
        
        return Response(data)


class CoachReviewsView(APIView):
    """
    GET /api/auth/coaches/<id>/reviews/
    Returns reviews for a coach (placeholder for now)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, coach_id):
        # Placeholder - implement reviews system later
        return Response([])
