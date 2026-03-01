from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

User = get_user_model()


@api_view(['POST'])
def request_password_reset(request):
    """
    Request password reset - sends email with reset link
    POST /api/auth/password-reset/request/
    Body: { "email": "user@example.com" }
    """
    email = request.data.get('email')
    
    if not email:
        return Response(
            {'error': 'Email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal if user exists or not for security
        return Response(
            {'message': 'If an account with that email exists, a password reset link has been sent.'},
            status=status.HTTP_200_OK
        )
    
    # Generate token
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Create reset link
    reset_link = f"{settings.FRONTEND_URL}/auth/reset-password?uid={uid}&token={token}"
    
    # Send email
    try:
        send_mail(
            subject='Password Reset Request - Smart Athlete',
            message=f'''
Hello {user.username},

You requested to reset your password. Click the link below to reset it:

{reset_link}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
Smart Athlete Team
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending email: {e}")
        # Still return success to not reveal if user exists
    
    return Response(
        {'message': 'If an account with that email exists, a password reset link has been sent.'},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
def reset_password(request):
    """
    Reset password with token
    POST /api/auth/password-reset/confirm/
    Body: { "uid": "...", "token": "...", "new_password": "..." }
    """
    uid = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    
    if not all([uid, token, new_password]):
        return Response(
            {'error': 'UID, token, and new password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate password strength
    if len(new_password) < 8:
        return Response(
            {'error': 'Password must be at least 8 characters long'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Decode user ID
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {'error': 'Invalid reset link'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check token validity
    if not default_token_generator.check_token(user, token):
        return Response(
            {'error': 'Invalid or expired reset link'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    return Response(
        {'message': 'Password has been reset successfully'},
        status=status.HTTP_200_OK
    )
