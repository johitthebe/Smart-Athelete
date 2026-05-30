from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from .activity_models import UserActivity
from django.utils import timezone
from datetime import timedelta
import random
import string

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
    
    # Coach capacity management
    accepting_requests = models.BooleanField(
        default=True,
        help_text="Whether coach is accepting new athlete requests"
    )
    max_athletes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Maximum number of athletes this coach can handle"
    )
    paused_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When coach paused accepting requests"
    )
    pause_reason = models.TextField(
        blank=True,
        help_text="Reason for pausing requests"
    )
    
    # Profile picture
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        help_text="User profile picture"
    )
    
    class Meta:
        # Ensure email is unique at database level
        constraints = [
            models.UniqueConstraint(fields=['email'], name='unique_email')
        ]
        indexes = [
            models.Index(
                fields=['role', 'accepting_requests'],
                name='coach_accepting_idx',
                condition=models.Q(role='coach', accepting_requests=True)
            ),
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


class CoachAthleteAssignment(models.Model):
    """Model to manage coach-athlete assignments"""
    ENDED_BY_CHOICES = (
        ('coach', 'Coach'),
        ('athlete', 'Athlete'),
        ('admin', 'Admin'),
    )
    
    coach = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assigned_athletes',
        limit_choices_to={'role': 'coach'}
    )
    athlete = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assigned_coaches',
        limit_choices_to={'role': 'athlete'}
    )
    request = models.ForeignKey(
        'CoachRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignment',
        help_text="Original request that created this assignment"
    )
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        related_name='assignments_made',
        limit_choices_to={'role': 'admin'}
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, help_text="Admin notes about this assignment")
    
    # End tracking
    ended_at = models.DateTimeField(null=True, blank=True)
    ended_by = models.CharField(max_length=20, choices=ENDED_BY_CHOICES, null=True, blank=True)
    end_reason = models.TextField(blank=True, help_text="Reason for ending assignment")
    
    class Meta:
        ordering = ['-assigned_at']
        unique_together = ['coach', 'athlete']
        indexes = [
            models.Index(fields=['coach', 'is_active']),
            models.Index(fields=['athlete', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.coach.get_full_name()} → {self.athlete.get_full_name()}"


class AthleteProfile(models.Model):
    """Comprehensive athlete profile from onboarding wizard"""
    
    # Relationship
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='athlete_profile')
    
    # Step 1: Account & Profile
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    )
    HEIGHT_UNIT_CHOICES = (
        ('cm', 'Centimeters'),
        ('ft', 'Feet'),
    )
    WEIGHT_UNIT_CHOICES = (
        ('kg', 'Kilograms'),
        ('lbs', 'Pounds'),
    )
    BODY_TYPE_CHOICES = (
        ('ectomorph', 'Ectomorph'),
        ('mesomorph', 'Mesomorph'),
        ('endomorph', 'Endomorph'),
        ('not_sure', 'Not Sure'),
    )
    
    age = models.IntegerField(validators=[MinValueValidator(13), MaxValueValidator(120)])
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    height = models.FloatField(validators=[MinValueValidator(0.1)])
    height_unit = models.CharField(max_length=5, choices=HEIGHT_UNIT_CHOICES, default='cm')
    weight = models.FloatField(validators=[MinValueValidator(0.1)])
    weight_unit = models.CharField(max_length=5, choices=WEIGHT_UNIT_CHOICES, default='kg')
    body_type = models.CharField(max_length=20, choices=BODY_TYPE_CHOICES)
    
    # Step 2: Fitness Background
    FITNESS_LEVEL_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('elite', 'Elite'),
    )
    
    fitness_level = models.CharField(max_length=20, choices=FITNESS_LEVEL_CHOICES)
    primary_sport = models.CharField(max_length=100)
    years_training = models.FloatField(validators=[MinValueValidator(0)])
    current_performance_baseline = models.TextField()
    
    # Step 3: Goals
    PRIMARY_GOAL_CHOICES = (
        ('weight_loss', 'Weight Loss'),
        ('muscle_gain', 'Muscle Gain'),
        ('endurance', 'Endurance'),
        ('strength', 'Strength'),
        ('speed', 'Speed'),
        ('flexibility', 'Flexibility'),
        ('general_fitness', 'General Fitness'),
    )
    GOAL_TIMEFRAME_CHOICES = (
        ('1_month', '1 Month'),
        ('3_months', '3 Months'),
        ('6_months', '6 Months'),
        ('1_year', '1 Year'),
        ('ongoing', 'Ongoing'),
    )
    
    primary_goal = models.CharField(max_length=20, choices=PRIMARY_GOAL_CHOICES)
    goal_timeframe = models.CharField(max_length=20, choices=GOAL_TIMEFRAME_CHOICES)
    target_event = models.CharField(max_length=200, blank=True)
    target_event_date = models.DateField(null=True, blank=True)
    
    # Step 4: Training Preferences
    INTENSITY_CHOICES = (
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('varied', 'Varied'),
    )
    TRAINING_TIME_CHOICES = (
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
        ('flexible', 'Flexible'),
    )
    
    weekly_availability = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(7)])
    preferred_intensity = models.CharField(max_length=20, choices=INTENSITY_CHOICES)
    preferred_training_time = models.CharField(max_length=20, choices=TRAINING_TIME_CHOICES)
    equipment_access = models.JSONField(default=list)
    
    # Step 5: Health & Motivation
    ACTIVITY_LEVEL_CHOICES = (
        ('sedentary', 'Sedentary'),
        ('lightly_active', 'Lightly Active'),
        ('moderately_active', 'Moderately Active'),
        ('very_active', 'Very Active'),
        ('extremely_active', 'Extremely Active'),
    )
    GUIDANCE_PREFERENCE_CHOICES = (
        ('self_directed', 'Self Directed'),
        ('structured_plan', 'Structured Plan'),
        ('coach_guided', 'Coach Guided'),
    )
    
    injury_history = models.TextField(blank=True)
    medical_conditions = models.TextField(blank=True)
    current_activity_level = models.CharField(max_length=20, choices=ACTIVITY_LEVEL_CHOICES)
    motivation_level = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    guidance_preference = models.CharField(max_length=20, choices=GUIDANCE_PREFERENCE_CHOICES)
    
    # Timestamps
    completed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['fitness_level']),
            models.Index(fields=['primary_goal']),
        ]
    
    def __str__(self):
        return f"Profile: {self.user.get_full_name()} - {self.fitness_level}"


class EmailVerificationOTP(models.Model):
    """Model to store email verification OTPs"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_otps')
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['otp_code', 'expires_at']),
        ]
    
    def __str__(self):
        return f"OTP for {self.user.email} - {self.otp_code}"
    
    def is_valid(self):
        """Check if OTP is still valid"""
        return not self.is_used and timezone.now() < self.expires_at
    
    @staticmethod
    def generate_otp():
        """Generate a 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    @classmethod
    def create_otp(cls, user):
        """Create a new OTP for user"""
        otp_code = cls.generate_otp()
        expires_at = timezone.now() + timedelta(minutes=10)  # OTP valid for 10 minutes
        return cls.objects.create(
            user=user,
            otp_code=otp_code,
            expires_at=expires_at
        )
