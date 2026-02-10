from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from .models import Goal, Benchmark, PerformanceLog
from .serializers import (
    GoalSerializer,
    BenchmarkSerializer,
    PerformanceLogSerializer,
)

User = get_user_model()


def is_super_admin(user):
    return getattr(user, "role", None) == "admin" or user.is_superuser


class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Goal.objects.filter(athlete=self.request.user)

    @action(detail=False, methods=["get"])
    def active(self, request):
        goals = self.get_queryset().filter(status="active")
        serializer = self.get_serializer(goals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def completed(self, request):
        goals = self.get_queryset().filter(status="completed")
        serializer = self.get_serializer(goals, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def mark_completed(self, request, pk=None):
        goal = self.get_object()
        goal.status = "completed"
        goal.save()
        serializer = self.get_serializer(goal)
        return Response(serializer.data)


class BenchmarkViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Benchmark.objects.all()
    serializer_class = BenchmarkSerializer
    permission_classes = [permissions.IsAuthenticated]


class PerformanceLogViewSet(viewsets.ModelViewSet):
    serializer_class = PerformanceLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PerformanceLog.objects.filter(
            athlete=self.request.user
        ).order_by("-date_logged")

    @action(detail=False, methods=["get"])
    def by_event(self, request):
        event = request.query_params.get("event")
        if event:
            logs = self.get_queryset().filter(event=event)
            serializer = self.get_serializer(logs, many=True)
            return Response(serializer.data)
        return Response(
            {"error": "event parameter required"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class AdminStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not is_super_admin(request.user):
            return Response(
                {"detail": "Forbidden"},
                status=status.HTTP_403_FORBIDDEN,
            )

        total_athletes = User.objects.filter(role="athlete").count()
        total_coaches = User.objects.filter(role="coach").count()
        active_goals = Goal.objects.filter(status="active").count()

        return Response(
            {
                "total_athletes": total_athletes,
                "total_coaches": total_coaches,
                "active_goals": active_goals,
            }
        )
