from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):

    ROLE_CHOICES = (
        ("athlete", "Athlete"),
        ("coach_pending", "Coach Pending"),
        ("coach", "Coach"),
        ("admin", "Admin"),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="athlete",
    )
    
    # Override email to make it unique and required
    email = models.EmailField(
        unique=True,
        blank=False,
        null=False,
        error_messages={
            'unique': "This email is already registered.",
        }
    )
    
    class Meta:
        # Ensure email is unique at database level
        constraints = [
            models.UniqueConstraint(fields=['email'], name='unique_email')
        ]


class CoachCredential(models.Model):
    """Model to store coach credentials/certifications"""
    coach = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credentials')
    credential_type = models.CharField(max_length=100)  # e.g., "Certification", "License", "Diploma"
    credential_name = models.CharField(max_length=200)
    issuing_organization = models.CharField(max_length=200)
    issue_date = models.DateField()
    file = models.FileField(upload_to='coach_credentials/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.credential_name} - {self.coach.get_full_name()}"


class CoachApproval(models.Model):
    """Model to track coach approval status and history"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    coach = models.OneToOneField(User, on_delete=models.CASCADE, related_name='approval')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_coaches')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.coach.get_full_name()} - {self.status}"
