from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Avg, Sum, Count
from django.utils import timezone
from datetime import timedelta
from .report_models import PerformanceReport
from .report_serializers import PerformanceReportSerializer, PerformanceReportListSerializer
from .models import PerformanceLog


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


class PerformanceAnalyticsView(APIView):
    """
    Returns analytics data for the authenticated athlete based on time range.
    Query param: range = week | month | year
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        range_param = request.query_params.get('range', 'month')

        now = timezone.now().date()
        if range_param == 'week':
            start_date = now - timedelta(days=7)
        elif range_param == 'year':
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=30)

        logs = PerformanceLog.objects.filter(
            athlete=request.user,
            date__gte=start_date,
        ).select_related('activity_type').order_by('date')

        total_sessions = logs.count()

        if total_sessions == 0:
            return Response({
                'total_sessions': 0,
                'avg_intensity': 0,
                'total_distance': 0,
                'improvement_rate': 0,
                'progress_data': [],
                'activity_breakdown': [],
            })

        agg = logs.aggregate(
            avg_intensity=Avg('intensity'),
            total_distance=Sum('distance'),
        )

        # Progress data: one point per log (date + distance or duration as value)
        progress_data = []
        for log in logs:
            value = float(log.distance or 0) or float(log.duration or 0) / 60
            progress_data.append({'date': str(log.date), 'value': round(value, 2)})

        # Improvement rate: compare first half vs second half avg value
        half = total_sessions // 2
        if half > 0:
            first_vals = [p['value'] for p in progress_data[:half]]
            second_vals = [p['value'] for p in progress_data[half:]]
            first_avg = sum(first_vals) / len(first_vals) if first_vals else 0
            second_avg = sum(second_vals) / len(second_vals) if second_vals else 0
            improvement = ((second_avg - first_avg) / first_avg * 100) if first_avg else 0
        else:
            improvement = 0

        # Activity breakdown
        activity_agg = (
            logs.values('activity_type__name')
            .annotate(count=Count('id'), avg_intensity=Avg('intensity'))
            .order_by('-count')
        )
        activity_breakdown = [
            {
                'name': item['activity_type__name'] or 'Unknown',
                'count': item['count'],
                'avg_intensity': round(float(item['avg_intensity'] or 0), 2),
            }
            for item in activity_agg
        ]

        return Response({
            'total_sessions': total_sessions,
            'avg_intensity': round(float(agg['avg_intensity'] or 0), 2),
            'total_distance': round(float(agg['total_distance'] or 0), 2),
            'improvement_rate': round(improvement, 2),
            'progress_data': progress_data,
            'activity_breakdown': activity_breakdown,
        })
