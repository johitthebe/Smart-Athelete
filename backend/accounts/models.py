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
