from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import CoachCredential, CoachApproval
from datetime import date
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


class CoachCredentialModelTest(TestCase):
    """Test the CoachCredential model"""
    
    def setUp(self):
        self.coach = User.objects.create_user(
            username='testcoach',
            email='coach@test.com',
            password='testpass123',
            role='coach_pending'
        )
    
    def test_create_coach_credential(self):
        """Test creating a coach credential"""
        # Create a simple test file
        test_file = SimpleUploadedFile(
            "test_cert.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        credential = CoachCredential.objects.create(
            coach=self.coach,
            credential_type='Certification',
            credential_name='CPR Certification',
            issuing_organization='Red Cross',
            issue_date=date(2024, 1, 1),
            file=test_file
        )
        
        self.assertEqual(credential.coach, self.coach)
        self.assertEqual(credential.credential_type, 'Certification')
        self.assertEqual(credential.credential_name, 'CPR Certification')
        self.assertEqual(credential.issuing_organization, 'Red Cross')
        self.assertIsNotNone(credential.uploaded_at)
    
    def test_coach_credentials_relationship(self):
        """Test the relationship between coach and credentials"""
        test_file = SimpleUploadedFile("cert.pdf", b"content", content_type="application/pdf")
        
        CoachCredential.objects.create(
            coach=self.coach,
            credential_type='License',
            credential_name='Coaching License',
            issuing_organization='Sports Authority',
            issue_date=date(2024, 1, 1),
            file=test_file
        )
        
        self.assertEqual(self.coach.credentials.count(), 1)
        self.assertEqual(self.coach.credentials.first().credential_name, 'Coaching License')


class CoachApprovalModelTest(TestCase):
    """Test the CoachApproval model"""
    
    def setUp(self):
        self.coach = User.objects.create_user(
            username='testcoach',
            email='coach@test.com',
            password='testpass123',
            role='coach_pending'
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='adminpass123',
            role='admin',
            is_staff=True
        )
    
    def test_create_coach_approval(self):
        """Test creating a coach approval record"""
        approval = CoachApproval.objects.create(
            coach=self.coach,
            status='pending'
        )
        
        self.assertEqual(approval.coach, self.coach)
        self.assertEqual(approval.status, 'pending')
        self.assertIsNone(approval.rejection_reason)
        self.assertIsNone(approval.reviewed_by)
        self.assertIsNone(approval.reviewed_at)
        self.assertIsNotNone(approval.created_at)
    
    def test_approve_coach(self):
        """Test approving a coach"""
        from django.utils import timezone
        
        approval = CoachApproval.objects.create(
            coach=self.coach,
            status='pending'
        )
        
        # Approve the coach
        approval.status = 'approved'
        approval.reviewed_by = self.admin
        approval.reviewed_at = timezone.now()
        approval.save()
        
        self.assertEqual(approval.status, 'approved')
        self.assertEqual(approval.reviewed_by, self.admin)
        self.assertIsNotNone(approval.reviewed_at)
    
    def test_reject_coach(self):
        """Test rejecting a coach"""
        from django.utils import timezone
        
        approval = CoachApproval.objects.create(
            coach=self.coach,
            status='pending'
        )
        
        # Reject the coach
        approval.status = 'rejected'
        approval.rejection_reason = 'Insufficient qualifications'
        approval.reviewed_by = self.admin
        approval.reviewed_at = timezone.now()
        approval.save()
        
        self.assertEqual(approval.status, 'rejected')
        self.assertEqual(approval.rejection_reason, 'Insufficient qualifications')
        self.assertEqual(approval.reviewed_by, self.admin)
        self.assertIsNotNone(approval.reviewed_at)
    
    def test_coach_approval_relationship(self):
        """Test the one-to-one relationship between coach and approval"""
        approval = CoachApproval.objects.create(
            coach=self.coach,
            status='pending'
        )
        
        self.assertEqual(self.coach.approval, approval)
        self.assertEqual(approval.coach, self.coach)
