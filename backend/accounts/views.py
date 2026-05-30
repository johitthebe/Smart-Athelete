from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, update_session_auth_hash
from .serializers import UserSerializer
from .activity_utils import log_activity
from .models import EmailVerificationOTP
from .otp_views import send_otp_email


@api_view(["POST"])
@permission_classes([AllowAny])
def register_api(request):
    """
    Register a new user and send OTP verification email.
    """
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        # Create user (serializer sets is_active=False by default)
        user = serializer.save()
        
        # Create OTP for email verification
        otp = EmailVerificationOTP.create_otp(user)
        
        # Send OTP email
        try:
            email_sent = send_otp_email(user, otp.otp_code)
        except Exception as e:
            print(f"Error in send_otp_email: {e}")
            email_sent = False
        
        # Log activity
        try:
            log_activity(
                user=user,
                action_type='user_registered',
                description=f"{user.username} registered as {user.role}",
                metadata={'role': user.role, 'email': user.email},
                request=request
            )
        except Exception as e:
            print(f"Error logging activity: {e}")
        
        # Always return consistent response format
        if not email_sent:
            return Response(
                {
                    "message": "Account created but verification email failed to send. Please use resend option.",
                    "email": user.email,
                    "requires_verification": True,
                    "email_sent": False
                },
                status=status.HTTP_201_CREATED,
            )
        
        return Response(
            {
                "message": "Registration successful. Please check your email for verification code.",
                "email": user.email,
                "requires_verification": True,
                "email_sent": True
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_profile_picture(request):
    """
    Upload or update user profile picture
    POST /api/auth/profile-picture/
    """
    if 'profile_picture' not in request.FILES:
        return Response(
            {"error": "No file provided"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    file = request.FILES['profile_picture']
    
    # Validate file type
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    file_ext = file.name.lower()[file.name.rfind('.'):]
    if file_ext not in allowed_extensions:
        return Response(
            {"error": "Invalid file type. Please upload JPG, PNG, GIF, or WEBP"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate file size (5MB max)
    if file.size > 5242880:
        return Response(
            {"error": "File size exceeds 5MB limit"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Delete old profile picture if exists
    if request.user.profile_picture:
        request.user.profile_picture.delete(save=False)
    
    # Save new profile picture
    request.user.profile_picture = file
    request.user.save()
    
    # Log activity
    log_activity(
        user=request.user,
        action_type='profile_updated',
        description=f"{request.user.username} updated profile picture",
        metadata={'action': 'profile_picture_upload'},
        request=request
    )
    
    # Return updated user data
    serializer = UserSerializer(request.user, context={'request': request})
    return Response(
        {
            "message": "Profile picture updated successfully",
            "user": serializer.data
        },
        status=status.HTTP_200_OK
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_profile_picture(request):
    """
    Delete user profile picture
    DELETE /api/auth/profile-picture/
    """
    if not request.user.profile_picture:
        return Response(
            {"error": "No profile picture to delete"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Delete profile picture
    request.user.profile_picture.delete(save=True)
    
    # Log activity
    log_activity(
        user=request.user,
        action_type='profile_updated',
        description=f"{request.user.username} deleted profile picture",
        metadata={'action': 'profile_picture_delete'},
        request=request
    )
    
    return Response(
        {"message": "Profile picture deleted successfully"},
        status=status.HTTP_200_OK
    )


from django.contrib.auth import authenticate, login as auth_login

@api_view(["POST"])
@permission_classes([AllowAny])
def login_api(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {"error": "Username and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(request, username=username, password=password)

    if not user:
        # Check if user exists but is inactive (unverified email)
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            inactive_user = User.objects.get(username=username)
            if not inactive_user.is_active:
                return Response(
                    {
                        "error": "Email not verified. Please verify your email to login.",
                        "email": inactive_user.email,
                        "requires_verification": True
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        except User.DoesNotExist:
            pass
        
        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Create session so subsequent requests are authenticated
    auth_login(request, user)
    
    # Log activity
    log_activity(
        user=user,
        action_type='user_login',
        description=f"{user.username} logged in",
        metadata={'role': user.role},
        request=request
    )

    return Response(
        {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": getattr(user, "role", None),
            },
        },
        status=status.HTTP_200_OK,
    )

from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from accounts.models import CoachCredential, CoachApproval
from accounts.serializers import CoachCredentialSerializer, CoachApprovalSerializer
from api.models import AdminNotification
from django.contrib.auth import get_user_model

User = get_user_model()


class CoachCredentialUploadView(APIView):
    """
    API endpoint for coaches to upload credentials
    POST /api/auth/coach/credentials/
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        # Verify user is a coach
        if request.user.role not in ['coach_pending', 'coach']:
            return Response(
                {"error": "Only coaches can upload credentials"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate file type
        file = request.FILES.get('file')
        if not file:
            return Response(
                {"error": "File is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check file extension
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.docx']
        file_ext = file.name.lower()[file.name.rfind('.'):]
        if file_ext not in allowed_extensions:
            return Response(
                {"error": "File type not supported. Please upload PDF, JPG, PNG, or DOCX"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check file size (10MB = 10485760 bytes)
        if file.size > 10485760:
            return Response(
                {"error": "File size exceeds 10MB limit"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create credential
        serializer = CoachCredentialSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            credential = serializer.save(coach=request.user)
            
            # Check if this is first upload or resubmission
            is_resubmission = False
            try:
                approval = CoachApproval.objects.get(coach=request.user)
                if approval.status == 'rejected':
                    is_resubmission = True
            except CoachApproval.DoesNotExist:
                # Create approval record if it doesn't exist
                CoachApproval.objects.create(coach=request.user, status='pending')
            
            # Create notification for all admins
            notification_type = 'coach_resubmitted' if is_resubmission else 'coach_credentials_submitted'
            message = f"Coach {request.user.get_full_name() or request.user.username} has {'resubmitted' if is_resubmission else 'submitted'} credentials for review"
            
            AdminNotification.objects.create(
                notification_type=notification_type,
                coach=request.user,
                message=message
            )
            
            return Response(
                {
                    "message": "Credentials submitted for review",
                    "credential": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CoachCredentialListView(APIView):
    """
    API endpoint to list coach's credentials
    GET /api/auth/coach/credentials/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role not in ['coach_pending', 'coach']:
            return Response(
                {"error": "Only coaches can view credentials"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        credentials = CoachCredential.objects.filter(coach=request.user)
        serializer = CoachCredentialSerializer(credentials, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class CoachCredentialDeleteView(APIView):
    """
    API endpoint to delete a credential
    DELETE /api/auth/coach/credentials/<id>/
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk):
        if request.user.role not in ['coach_pending', 'coach']:
            return Response(
                {"error": "Only coaches can delete credentials"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            credential = CoachCredential.objects.get(pk=pk, coach=request.user)
            credential.file.delete()  # Delete the file from storage
            credential.delete()
            return Response(
                {"message": "Credential deleted successfully"},
                status=status.HTTP_200_OK
            )
        except CoachCredential.DoesNotExist:
            return Response(
                {"error": "Credential not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class CoachStatusView(APIView):
    """
    API endpoint to get coach approval status
    GET /api/auth/coach/status/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role not in ['coach_pending', 'coach']:
            return Response(
                {"error": "Only coaches can view status"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            approval = CoachApproval.objects.get(coach=request.user)
            serializer = CoachApprovalSerializer(approval, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CoachApproval.DoesNotExist:
            # Create approval record if it doesn't exist
            approval = CoachApproval.objects.create(coach=request.user, status='pending')
            serializer = CoachApprovalSerializer(approval, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def me(request):
    """
    Get or update current user profile
    """
    if request.method == 'GET':
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    """
    Logout user and clear session
    """
    from django.contrib.auth import logout
    logout(request)
    return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Change user password
    """
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    if not old_password or not new_password:
        return Response(
            {'error': 'Both old and new passwords are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if old password is correct
    if not user.check_password(old_password):
        return Response(
            {'error': 'Current password is incorrect'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Set new password
    user.set_password(new_password)
    user.save()

    # Update session to prevent logout
    update_session_auth_hash(request, user)

    return Response({
        'message': 'Password changed successfully'
    })
