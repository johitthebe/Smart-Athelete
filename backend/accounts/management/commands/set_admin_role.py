from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'Set a user as admin by username'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user to make admin')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
            user.role = 'admin'
            user.save()
            
            self.stdout.write(self.style.SUCCESS(f'✓ Successfully set {username} as admin!'))
            self.stdout.write(f'  ID: {user.id}')
            self.stdout.write(f'  Username: {user.username}')
            self.stdout.write(f'  Email: {user.email}')
            self.stdout.write(f'  Role: {user.role}')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'✗ User "{username}" not found!'))
            self.stdout.write('\nAvailable users:')
            for u in User.objects.all():
                self.stdout.write(f'  - {u.username} (ID: {u.id}, Role: {u.role})')
