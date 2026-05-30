from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import EmailVerificationOTP
from .activity_utils import log_activity

User = get_user_model()


def send_otp_email(user, otp_code):
    """Send OTP verification email to user"""
    subject = 'Verify Your Email - Smart Athlete'
    message = f"""
Hello {user.first_name or user.username},

Thank you for registering with Smart Athlete!

Your email verification code is: {otp_code}

This code will expire in 10 minutes.

If you didn't create an account, please ignore this email.

Best regards,
Smart Athlete Team
    """
    
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #173B80;">Welcome to Smart Athlete!</h2>
                <p>Hello {user.first_name or user.username},</p>
                <p>Thank you for registering with Smart Athlete!</p>
                
                <div style="background-color: #f4f4f4; padding: 20px; border-radius: 5px; text-align: center; margin: 30px 0;">
                    <p style="margin: 0; font-size: 14px; color: #666;">Your verification code is:</p>
                    <h1 style="margin: 10px 0; color: #173B80; font-size: 36px; letter-spacing: 5px;">{otp_code}</h1>
                    <p style="margin: 0; font-size: 12px; color: #999;">This code will expire in 10 minutes</p>
                </div>
                
                <p>Enter this code on the verification page to activate your account.</p>
                <p style="color: #666; font-size: 14px;">If you didn't create an account, please ignore this email.</p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #999; font-size: 12px;">Best regards,<br>Smart Athlete Team</p>
            </div>
        </body>
    </html>
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending OTP email: {e}")
        return False


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_email_otp(request):
    """
    Verify email using OTP code
    POST /api/auth/verify-email/
    Body: { "email": "user@example.com", "otp_code": "123456" }
    """
    email = request.data.get("email")
    otp_code = request.data.get("otp_code")
    
    if not email or not otp_code:
        return Response(
            {"error": "Email and OTP code are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if user is already active
    if user.is_active:
        return Response(
            {"message": "Email already verified"},
            status=status.HTTP_200_OK
        )
    
    # Find the most recent valid OTP
    try:
        otp = EmailVerificationOTP.objects.filter(
            user=user,
            otp_code=otp_code,
            is_used=False
        ).latest('created_at')
    except EmailVerificationOTP.DoesNotExist:
        return Response(
            {"error": "Invalid OTP code"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if OTP is expired
    if not otp.is_valid():
        return Response(
            {"error": "OTP code has expired. Please request a new one."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Mark OTP as used
    otp.is_used = True
    otp.save()
    
    # Activate user
    user.is_active = True
    user.save()
    
    # Log activity
    log_activity(
        user=user,
        action_type='email_verified',
        description=f"{user.username} verified their email",
        metadata={'email': user.email},
        request=request
    )
    
    return Response(
        {
            "message": "Email verified successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            }
        },
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def resend_otp(request):
    """
    Resend OTP verification email
    POST /api/auth/resend-otp/
    Body: { "email": "user@example.com" }
    """
    email = request.data.get("email")
    
    if not email:
        return Response(
            {"error": "Email is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if user is already active
    if user.is_active:
        return Response(
            {"error": "Email already verified"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check rate limiting - prevent sending too many OTPs
    recent_otps = EmailVerificationOTP.objects.filter(
        user=user,
        created_at__gte=timezone.now() - timezone.timedelta(minutes=1)
    ).count()
    
    if recent_otps >= 3:
        return Response(
            {"error": "Too many requests. Please wait a minute before requesting a new code."},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    # Create new OTP
    otp = EmailVerificationOTP.create_otp(user)
    
    # Send email
    email_sent = send_otp_email(user, otp.otp_code)
    
    if not email_sent:
        return Response(
            {"error": "Failed to send email. Please try again later."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Log activity
    log_activity(
        user=user,
        action_type='otp_resent',
        description=f"OTP resent to {user.email}",
        metadata={'email': user.email},
        request=request
    )
    
    return Response(
        {"message": "Verification code sent successfully"},
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def check_verification_status(request):
    """
    Check if email is verified
    POST /api/auth/check-verification/
    Body: { "email": "user@example.com" }
    """
    email = request.data.get("email")
    
    if not email:
        return Response(
            {"error": "Email is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
        return Response(
            {
                "is_verified": user.is_active,
                "email": user.email
            },
            status=status.HTTP_200_OK
        )
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND
        )
