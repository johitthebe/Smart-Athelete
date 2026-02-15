from django.core.management.base import BaseCommand
from performance.models import ActivityType


class Command(BaseCommand):
    help = 'Seed default activity types for performance logging'

    def handle(self, *args, **kwargs):
        activity_types = [
            {'name': 'Running', 'icon': '🏃', 'requires_distance': True, 'requires_duration': True},
            {'name': 'Cycling', 'icon': '🚴', 'requires_distance': True, 'requires_duration': True},
            {'name': 'Swimming', 'icon': '🏊', 'requires_distance': True, 'requires_duration': True},
            {'name': 'Weight Training', 'icon': '🏋️', 'requires_distance': False, 'requires_duration': True},
            {'name': 'Yoga', 'icon': '🧘', 'requires_distance': False, 'requires_duration': True},
            {'name': 'Walking', 'icon': '🚶', 'requires_distance': True, 'requires_duration': True},
            {'name': 'Hiking', 'icon': '🥾', 'requires_distance': True, 'requires_duration': True},
            {'name': 'Rowing', 'icon': '🚣', 'requires_distance': True, 'requires_duration': True},
            {'name': 'CrossFit', 'icon': '💪', 'requires_distance': False, 'requires_duration': True},
            {'name': 'Boxing', 'icon': '🥊', 'requires_distance': False, 'requires_duration': True},
        ]

        created_count = 0
        for activity_data in activity_types:
            activity, created = ActivityType.objects.get_or_create(
                name=activity_data['name'],
                defaults={
                    'icon': activity_data['icon'],
                    'requires_distance': activity_data['requires_distance'],
                    'requires_duration': activity_data['requires_duration'],
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created activity type: {activity.icon} {activity.name}')
                )

        if created_count == 0:
            self.stdout.write(self.style.WARNING('All activity types already exist'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} activity types')
            )
