from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.files.uploadedfile import UploadedFile
from accounts.models import CoachCredential, CoachApproval, User
from accounts.serializers import CoachCredentialSerializer, CoachApprovalSerializer
from api.models import AdminNotification
import os


# Allowed file types and max size
ALLOWED_FILE_TYPES = ['.pdf', '.jpg', '.jpeg', '.png', '.docx']
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes


def validate_file(file: UploadedFile):
    """Validate file type and size"""
    errors = []
    
    # Check file size
    if file.size > MAX_FILE_SIZE:
        errors.append(f"File size exceeds maximum allowed size of 10MB")
    
    # Check file type
    file_ext = os.path.splitext(file.name)[1].lower()
    if file_ext not in ALLOWED_FILE_TYPES:
        errors.append(f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_FILE_TYPES)}")
    
    return errors


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_credential(request):
    """
    Upload a coach credential
    POST /api/auth/coach/credentials/
    """
    user = request.user
    
    # Check if user is a coach
    if user.role not in ['coach', 'coach_pending']:
        return Response(
            {"error": "Only coaches can upload credentials"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Validate required fields
    required_fields = ['credential_type', 'credential_name', 'issuing_organization', 'issue_date']
    for field in required_fields:
        if field not in request.data:
            return Response(
                {"error": f"Field '{field}' is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Validate file
    if 'file' not in request.FILES:
        return Response(
            {"error": "File is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    file = request.FILES['file']
    file_errors = validate_file(file)
    if file_errors:
        return Response(
            {"error": file_errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create credential
    credential_data = {
        'credential_type': request.data.get('credential_type'),
        'credential_name': request.data.get('credential_name'),
        'issuing_organization': request.data.get('issuing_organization'),
        'issue_date': request.data.get('issue_date'),
        'file': file
    }
    
    serializer = CoachCredentialSerializer(data=credential_data, context={'request': request})
    if serializer.is_valid():
        # Save with coach explicitly set
        credential = serializer.save(coach=user)
        
        # Check if this is first upload or resubmission
        credential_count = user.credentials.count()
        is_first_upload = credential_count == 1
        
        # Create notifications for all admin users
        admin_users = User.objects.filter(role='admin')
        notification_type = 'new_submission' if is_first_upload else 'resubmission'
        
        for admin in admin_users:
            AdminNotification.objects.create(
                notification_type=notification_type,
                coach=user,
                message=f"{user.get_full_name()} has {'submitted' if is_first_upload else 'resubmitted'} credentials for review"
            )
        
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_credentials(request):
    """
    List all credentials for authenticated coach
    GET /api/auth/coach/credentials/
    """
    user = request.user
    
    # Check if user is a coach
    if user.role not in ['coach', 'coach_pending']:
        return Response(
            {"error": "Only coaches can view credentials"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    credentials = CoachCredential.objects.filter(coach=user).order_by('-uploaded_at')
    serializer = CoachCredentialSerializer(credentials, many=True, context={'request': request})
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_credential(request, credential_id):
    """
    Delete a credential
    DELETE /api/auth/coach/credentials/<id>/
    """
    user = request.user
    
    # Check if user is a coach
    if user.role not in ['coach', 'coach_pending']:
        return Response(
            {"error": "Only coaches can delete credentials"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        credential = CoachCredential.objects.get(id=credential_id, coach=user)
    except CoachCredential.DoesNotExist:
        return Response(
            {"error": "Credential not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Delete file from storage
    if credential.file:
        credential.file.delete()
    
    # Delete database record
    credential.delete()
    
    return Response(
        {"message": "Credential deleted successfully"},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def coach_status(request):
    """
    Get coach approval status
    GET /api/auth/coach/status/
    """
    user = request.user
    
    # Check if user is a coach
    if user.role not in ['coach', 'coach_pending']:
        return Response(
            {"error": "Only coaches can view status"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get or create approval record
    approval, created = CoachApproval.objects.get_or_create(coach=user)
    
    # Get credential count
    credential_count = user.credentials.count()
    
    return Response({
        'status': approval.status,
        'rejection_reason': approval.rejection_reason,
        'credential_count': credential_count,
        'reviewed_at': approval.reviewed_at,
        'reviewed_by': approval.reviewed_by.get_full_name() if approval.reviewed_by else None
    }, status=status.HTTP_200_OK)
