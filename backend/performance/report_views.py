from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .report_models import PerformanceReport
from .report_serializers import PerformanceReportSerializer, PerformanceReportListSerializer


class PerformanceReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for performance reports shared between athletes and coaches
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PerformanceReportListSerializer
        return PerformanceReportSerializer
    
    def get_queryset(self):
        """Return reports where user is athlete or coach"""
        user = self.request.user
        
        if user.role == 'athlete':
            # Athletes see their own submitted reports
            return PerformanceReport.objects.filter(athlete=user)
        elif user.role == 'coach':
            # Coaches see reports submitted to them
            return PerformanceReport.objects.filter(coach=user)
        else:
            return PerformanceReport.objects.none()
    
    def create(self, request, *args, **kwargs):
        """Athletes submit reports to their coaches"""
        if request.user.role != 'athlete':
            return Response(
                {"error": "Only athletes can submit reports"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate that the coach is assigned to this athlete
        coach_id = request.data.get('coach')
        if not coach_id:
            return Response(
                {"error": "Coach is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from accounts.models import CoachAthleteAssignment
        if not CoachAthleteAssignment.objects.filter(
            coach_id=coach_id,
            athlete=request.user,
            is_active=True
        ).exists():
            return Response(
                {"error": "You can only submit reports to coaches assigned to you"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending reports (for coaches)"""
        if request.user.role != 'coach':
            return Response(
                {"error": "Only coaches can access pending reports"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reports = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(reports, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def reviewed(self, request):
        """Get reviewed reports"""
        reports = self.get_queryset().filter(status__in=['reviewed', 'feedback_given'])
        serializer = self.get_serializer(reports, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def give_feedback(self, request, pk=None):
        """Coach gives feedback on a report"""
        if request.user.role != 'coach':
            return Response(
                {"error": "Only coaches can give feedback"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        report = self.get_object()
        
        # Verify coach owns this report
        if report.coach != request.user:
            return Response(
                {"error": "You can only give feedback on reports submitted to you"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        feedback = request.data.get('feedback', '')
        if not feedback:
            return Response(
                {"error": "Feedback is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        report.mark_reviewed(feedback)
        serializer = self.get_serializer(report)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_reviewed(self, request, pk=None):
        """Coach marks report as reviewed without feedback"""
        if request.user.role != 'coach':
            return Response(
                {"error": "Only coaches can mark reports as reviewed"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        report = self.get_object()
        
        # Verify coach owns this report
        if report.coach != request.user:
            return Response(
                {"error": "You can only review reports submitted to you"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        report.mark_reviewed()
        serializer = self.get_serializer(report)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_coaches(self, request):
        """Get list of coaches assigned to athlete (for report submission)"""
        if request.user.role != 'athlete':
            return Response(
                {"error": "Only athletes can access this endpoint"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from accounts.models import CoachAthleteAssignment
        from accounts.serializers import CoachAthleteAssignmentSerializer
        
        assignments = CoachAthleteAssignment.objects.filter(
            athlete=request.user,
            is_active=True
        ).select_related('coach')
        
        coaches = []
        for assignment in assignments:
            coaches.append({
                'id': assignment.coach.id,
                'name': assignment.coach.get_full_name() or assignment.coach.username,
                'username': assignment.coach.username,
                'email': assignment.coach.email
            })
        
        return Response(coaches)
