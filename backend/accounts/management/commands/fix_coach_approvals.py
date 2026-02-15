from django.core.management.base import BaseCommand
from accounts.models import User, CoachApproval


class Command(BaseCommand):
    help = 'Fix inconsistencies between coach roles and approval statuses'

    def handle(self, *args, **kwargs):
        # Fix coaches who have role='coach' but approval status is 'pending'
        inconsistent_approvals = CoachApproval.objects.filter(
            status='pending',
            coach__role='coach'
        )
        
        count = 0
        for approval in inconsistent_approvals:
            approval.status = 'approved'
            approval.save()
            count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Fixed approval for coach: {approval.coach.username}')
            )
        
        # Fix coaches who have role='coach_pending' but approval status is 'approved'
        inconsistent_pending = CoachApproval.objects.filter(
            status='approved',
            coach__role='coach_pending'
        )
        
        for approval in inconsistent_pending:
            approval.coach.role = 'coach'
            approval.coach.save()
            count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Fixed role for coach: {approval.coach.username}')
            )
        
        if count == 0:
            self.stdout.write(self.style.WARNING('No inconsistencies found'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully fixed {count} inconsistencies')
            )
