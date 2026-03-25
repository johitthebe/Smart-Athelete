from django.core.management.base import BaseCommand
from api.notification_utils import check_and_send_performance_reminders


class Command(BaseCommand):
    help = 'Send notifications to athletes who have not logged performance in the last 24 hours'

    def handle(self, *args, **options):
        self.stdout.write('Checking for athletes who need performance reminders...')
        
        notifications_sent = check_and_send_performance_reminders()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully sent {notifications_sent} performance reminders')
        )
