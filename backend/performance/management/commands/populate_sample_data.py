from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import models
from performance.models import Goal, PerformanceLog, ActivityType
from datetime import datetime, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate sample performance data for a user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to populate data for')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" does not exist'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Populating data for user: {username}'))
        
        # Get or create activity types
        running, _ = ActivityType.objects.get_or_create(
            name='Running',
            defaults={'icon': '🏃', 'requires_distance': True, 'requires_duration': True}
        )
        cycling, _ = ActivityType.objects.get_or_create(
            name='Cycling',
            defaults={'icon': '🚴', 'requires_distance': True, 'requires_duration': True}
        )
        swimming, _ = ActivityType.objects.get_or_create(
            name='Swimming',
            defaults={'icon': '🏊', 'requires_distance': True, 'requires_duration': True}
        )
        gym, _ = ActivityType.objects.get_or_create(
            name='Gym Workout',
            defaults={'icon': '💪', 'requires_distance': False, 'requires_duration': True}
        )
        
        # Create goals
        goal1, created = Goal.objects.get_or_create(
            athlete=user,
            name='Run 100km this month',
            defaults={
                'description': 'Build endurance by running 100km total',
                'activity_type': running,
                'target_metric': 'distance',
                'target_value': 100,
                'target_unit': 'km',
                'deadline': datetime.now() + timedelta(days=30),
                'status': 'active'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created goal: {goal1.name}'))
        
        goal2, created = Goal.objects.get_or_create(
            athlete=user,
            name='Cycle 200km this month',
            defaults={
                'description': 'Improve cycling endurance',
                'activity_type': cycling,
                'target_metric': 'distance',
                'target_value': 200,
                'target_unit': 'km',
                'deadline': datetime.now() + timedelta(days=30),
                'status': 'active'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created goal: {goal2.name}'))
        
        # Create performance logs for the past 30 days
        activities = [
            {'type': running, 'goal': goal1, 'distance_range': (3, 10), 'duration_range': (1200, 3600), 'calories_range': (200, 600)},
            {'type': cycling, 'goal': goal2, 'distance_range': (10, 30), 'duration_range': (1800, 5400), 'calories_range': (300, 900)},
            {'type': swimming, 'goal': goal1, 'distance_range': (1, 3), 'duration_range': (1200, 2400), 'calories_range': (250, 500)},
            {'type': gym, 'goal': goal1, 'distance_range': (0, 0), 'duration_range': (2400, 4800), 'calories_range': (300, 600)},
        ]
        
        logs_created = 0
        for i in range(30):
            # Create 1-2 logs per day
            num_logs = random.randint(1, 2)
            date = datetime.now() - timedelta(days=29-i)
            
            for _ in range(num_logs):
                activity = random.choice(activities)
                
                distance = random.uniform(*activity['distance_range']) if activity['distance_range'][1] > 0 else None
                duration = random.randint(*activity['duration_range'])
                calories = random.randint(*activity['calories_range'])
                intensity = random.randint(4, 9)
                
                # Add some progression (improvement over time)
                progression_factor = 1 + (i / 30) * 0.2  # 20% improvement over 30 days
                if distance:
                    distance *= progression_factor
                
                notes_options = [
                    "Felt great today!",
                    "Good workout, pushed hard",
                    "Steady pace, felt comfortable",
                    "Challenging but rewarding",
                    "Easy recovery session",
                    "Personal best!",
                    "Tough day but finished strong",
                    "Perfect weather for training"
                ]
                
                log, created = PerformanceLog.objects.get_or_create(
                    athlete=user,
                    goal=activity['goal'],
                    activity_type=activity['type'],
                    date=date.date(),
                    defaults={
                        'distance': round(distance, 2) if distance else None,
                        'duration': duration,
                        'calories': calories,
                        'intensity': intensity,
                        'notes': random.choice(notes_options)
                    }
                )
                
                if created:
                    logs_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {logs_created} performance logs'))
        
        # Update goal progress
        for goal in [goal1, goal2]:
            total_distance = PerformanceLog.objects.filter(
                athlete=user,
                goal=goal,
                distance__isnull=False
            ).aggregate(total=models.Sum('distance'))['total'] or 0
            
            goal.current_value = total_distance
            goal.save()
            
            self.stdout.write(self.style.SUCCESS(
                f'Updated goal "{goal.name}": {goal.current_value:.2f}/{goal.target_value} {goal.target_unit}'
            ))
        
        self.stdout.write(self.style.SUCCESS('Sample data population complete!'))
