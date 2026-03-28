from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count
from django.utils import timezone
from django.db import transaction
from .coach_request_models import CoachRequest, CoachCapacityLog
from .coach_request_serializers import (
    AvailableCoachSerializer,
    CoachRequestSerializer,
    CoachCapacityStatusSerializer,
    MyAthleteSerializer
)
from .models import User, CoachAthleteAssignment


class AvailableCoachesView(APIView):
    """
    GET /api/coaches/available/
    Returns list of coaches accepting requests
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if request.user.role != 'athlete':
            return Response(
                {"error": "Only athletes can browse coaches"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        coaches = User.objects.filter(
            role='coach',
            accepting_requests=True,
            is_active=True
        ).order_by('username')
        
        # Filter by search
        search = request.query_params.get('search')
        if search:
            coaches = coaches.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        serializer = AvailableCoachSerializer(coaches, many=True)
        return Response({"coaches": serializer.data})


class CoachRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for coach requests
    """
    serializer_class = CoachRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'athlete':
            return CoachRequest.objects.filter(athlete=user)
        elif user.role == 'coach':
            return CoachRequest.objects.filter(coach=user)
        return CoachRequest.objects.none()
    
    def create(self, request, *args, **kwargs):
        """Athlete requests a coach"""
        if request.user.role != 'athlete':
            return Response(
                {"error": "Only athletes can request coaches", "code": "NOT_ATHLETE"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        coach_id = request.data.get('coach')
        if not coach_id:
            return Response(
                {"error": "coach_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate coach exists and is accepting
        try:
            coach = User.objects.get(id=coach_id, role='coach')
        except User.DoesNotExist:
            return Response(
                {"error": "Coach not found", "code": "COACH_NOT_FOUND"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not coach.accepting_requests:
            return Response(
                {"error": "Coach is not accepting requests", "code": "COACH_NOT_ACCEPTING"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for duplicate pending request
        if CoachRequest.objects.filter(
            athlete=request.user,
            coach=coach,
            status='pending'
        ).exists():
            return Response(
                {"error": "You already have a pending request to this coach", "code": "DUPLICATE_REQUEST"},
                status=status.HTTP_409_CONFLICT
            )
        
        # Create the request
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(
            {
                "success": True,
                "request": serializer.data,
                "message": f"Request sent to {coach.get_full_name() or coach.username}"
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """Athlete views their requests"""
        if request.user.role != 'athlete':
            return Response(
                {"error": "Only athletes can view their requests"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        requests = self.get_queryset().order_by('-requested_at')
        serializer = self.get_serializer(requests, many=True)
        return Response({"requests": serializer.data})
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Coach views pending requests"""
        if request.user.role != 'coach':
            return Response(
                {"error": "Only coaches can view pending requests"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        requests = self.get_queryset().filter(status='pending').order_by('-requested_at')
        serializer = self.get_serializer(requests, many=True)
        return Response({"requests": serializer.data})
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Coach accepts a request"""
        if request.user.role != 'coach':
            return Response(
                {"error": "Only coaches can accept requests"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        coach_request = self.get_object()
        
        if coach_request.coach != request.user:
            return Response(
                {"error": "You are not the coach for this request", "code": "NOT_AUTHORIZED"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if coach_request.status != 'pending':
            return Response(
                {"error": "Request is not pending", "code": "INVALID_STATUS"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # First, mark any old accepted requests as expired to avoid unique constraint violation
            CoachRequest.objects.filter(
                coach=coach_request.coach,
                athlete=coach_request.athlete,
                status='accepted'
            ).exclude(id=coach_request.id).update(status='expired')
            
            # Create or get assignment (handle duplicate case)
            assignment, created = CoachAthleteAssignment.objects.get_or_create(
                coach=coach_request.coach,
                athlete=coach_request.athlete,
                defaults={'request': coach_request}
            )
            
            # If assignment already exists but was inactive, reactivate it
            if not created and not assignment.is_active:
                assignment.is_active = True
                assignment.request = coach_request
                assignment.save()
            
            # Update request
            coach_request.status = 'accepted'
            coach_request.responded_at = timezone.now()
            coach_request.save()
            
            # Check auto-pause
            check_auto_pause(request.user)
        
        return Response({
            "success": True,
            "assignment_id": assignment.id,
            "message": f"{coach_request.athlete.get_full_name()} is now your athlete"
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Coach rejects a request"""
        if request.user.role != 'coach':
            return Response(
                {"error": "Only coaches can reject requests"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        coach_request = self.get_object()
        
        if coach_request.coach != request.user:
            return Response(
                {"error": "You are not the coach for this request"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if coach_request.status != 'pending':
            return Response(
                {"error": "Request is not pending"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', '')
        coach_request.status = 'rejected'
        coach_request.rejection_reason = reason
        coach_request.responded_at = timezone.now()
        coach_request.save()
        
        return Response({
            "success": True,
            "message": "Request rejected"
        })
    
    def destroy(self, request, *args, **kwargs):
        """Athlete cancels their request"""
        if request.user.role != 'athlete':
            return Response(
                {"error": "Only athletes can cancel requests"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        coach_request = self.get_object()
        
        if coach_request.status != 'pending':
            return Response(
                {"error": "Can only cancel pending requests"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        coach_request.status = 'cancelled'
        coach_request.save()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class CoachCapacityView(APIView):
    """
    Coach capacity management endpoints
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """GET /api/coaches/capacity-status/"""
        if request.user.role != 'coach':
            return Response(
                {"error": "Only coaches can view capacity status"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        current_athletes = CoachAthleteAssignment.objects.filter(
            coach=request.user,
            is_active=True
        ).count()
        
        pending_requests = CoachRequest.objects.filter(
            coach=request.user,
            status='pending'
        ).count()
        
        capacity_available = None
        if request.user.max_athletes:
            capacity_available = request.user.max_athletes - current_athletes
        
        data = {
            'accepting_requests': request.user.accepting_requests,
            'max_athletes': request.user.max_athletes,
            'current_athletes': current_athletes,
            'capacity_available': capacity_available,
            'paused_at': request.user.paused_at,
            'pause_reason': request.user.pause_reason or '',
            'pending_requests': pending_requests
        }
        
        serializer = CoachCapacityStatusSerializer(data)
        return Response(serializer.data)


class CoachPauseRequestsView(APIView):
    """POST /api/coaches/pause-requests/"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        if request.user.role != 'coach':
            return Response(
                {"error": "Only coaches can pause requests"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not request.user.accepting_requests:
            return Response(
                {"error": "Already paused"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reason = request.data.get('reason', '')
        current_athletes = CoachAthleteAssignment.objects.filter(
            coach=request.user,
            is_active=True
        ).count()
        
        request.user.accepting_requests = False
        request.user.paused_at = timezone.now()
        request.user.pause_reason = reason
        request.user.save()
        
        CoachCapacityLog.objects.create(
            coach=request.user,
            action='paused',
            athlete_count=current_athletes,
            reason=reason
        )
        
        return Response({
            "success": True,
            "accepting_requests": False,
            "current_athletes": current_athletes
        })


class CoachResumeRequestsView(APIView):
    """POST /api/coaches/resume-requests/"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        if request.user.role != 'coach':
            return Response(
                {"error": "Only coaches can resume requests"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.user.accepting_requests:
            return Response(
                {"error": "Not paused"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        current_athletes = CoachAthleteAssignment.objects.filter(
            coach=request.user,
            is_active=True
        ).count()
        
        request.user.accepting_requests = True
        request.user.paused_at = None
        request.user.pause_reason = ''
        request.user.save()
        
        CoachCapacityLog.objects.create(
            coach=request.user,
            action='resumed',
            athlete_count=current_athletes
        )
        
        return Response({
            "success": True,
            "accepting_requests": True,
            "current_athletes": current_athletes
        })


class MyAthletesView(APIView):
    """GET /api/coaches/my-athletes/"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if request.user.role != 'coach':
            return Response(
                {"error": "Only coaches can view their athletes"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        assignments = CoachAthleteAssignment.objects.filter(
            coach=request.user,
            is_active=True
        ).select_related('athlete').order_by('-assigned_at')
        
        serializer = MyAthleteSerializer(assignments, many=True)
        
        return Response({
            "count": assignments.count(),
            "athletes": serializer.data
        })


def check_auto_pause(coach):
    """Check if coach should be auto-paused after accepting a request"""
    if not coach.max_athletes:
        return
    
    current_count = CoachAthleteAssignment.objects.filter(
        coach=coach,
        is_active=True
    ).count()
    
    if current_count >= coach.max_athletes:
        coach.accepting_requests = False
        coach.paused_at = timezone.now()
        coach.save()
        
        CoachCapacityLog.objects.create(
            coach=coach,
            action='auto_paused',
            athlete_count=current_count,
            reason=f'Reached max capacity: {coach.max_athletes}'
        )


class MyCoachesView(APIView):
    """GET /api/athlete/my-coaches/ - Get athlete's assigned coaches"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if request.user.role != 'athlete':
            return Response(
                {"error": "Only athletes can view their coaches"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        assignments = CoachAthleteAssignment.objects.filter(
            athlete=request.user,
            is_active=True
        ).select_related('coach').order_by('-assigned_at')
        
        # Create serializer data manually
        coaches_data = []
        for assignment in assignments:
            coaches_data.append({
                'id': assignment.id,
                'coach': assignment.coach.id,
                'coach_name': assignment.coach.get_full_name() or assignment.coach.username,
                'coach_username': assignment.coach.username,
                'coach_email': assignment.coach.email,
                'assigned_at': assignment.assigned_at,
                'notes': assignment.notes
            })
        
        return Response({
            "count": len(coaches_data),
            "coaches": coaches_data
        })
