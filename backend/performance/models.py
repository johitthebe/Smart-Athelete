from django.conf import settings
from django.db import models
from django.utils import timezone


class Benchmark(models.Model):
    event = models.CharField(max_length=100)
    level = models.CharField(
        max_length=50,
        default="general",
        help_text="e.g., U18, U20, Elite"
    )
    benchmark_value = models.FloatField(help_text="e.g., 4.6 for 40m sprint in seconds")
    unit = models.CharField(max_length=20, default="seconds", help_text="seconds, meters, etc")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event} ({self.level}): {self.benchmark_value}{self.unit}"


class Goal(models.Model):
    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='goals'
    )
    event = models.CharField(max_length=100, help_text="e.g., 40m Sprint")
    target_value = models.FloatField(help_text="e.g., 4.5")
    current_value = models.FloatField(default=0.0, help_text="Best/latest performance")
    benchmark = models.ForeignKey(
        Benchmark,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='goals'
    )
    deadline = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=(
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('on_hold', 'On Hold'),
        ),
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.athlete} → {self.event} ({self.target_value})"

    def progress_percentage(self):
        if self.target_value == 0:
            return 0
        if self.benchmark and self.benchmark.benchmark_value:
            range_val = self.benchmark.benchmark_value - self.target_value
            if range_val == 0:
                return 0
            return ((self.current_value - self.target_value) / range_val) * 100
        return 0

    def check_completion(self):
        if self.current_value <= self.target_value and self.status == 'active':
            self.status = 'completed'
            self.save()


class PerformanceLog(models.Model):
    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='performance_logs'
    )
    event = models.CharField(max_length=100, help_text="e.g., 40m Sprint")
    value = models.FloatField(help_text="e.g., 4.9 seconds")
    intensity = models.IntegerField(
        default=5,
        help_text="1-10 scale"
    )
    notes = models.TextField(blank=True)
    date_logged = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.athlete} - {self.event}: {self.value}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            goal = Goal.objects.get(athlete=self.athlete, event=self.event, status='active')
            if goal.current_value == 0 or self.value < goal.current_value:
                goal.current_value = self.value
                goal.check_completion()
        except Goal.DoesNotExist:
       	    pass
