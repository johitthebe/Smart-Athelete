from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db import IntegrityError

from .serializers import UserSerializer
from accounts.models import User
from rest_framework.permissions import IsAuthenticated, AllowAny


# -----------------------------
# CSRF Endpoint
# -----------------------------
@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([AllowAny])
def get_csrf(request):
    return Response({"message": "CSRF cookie set"})


# -----------------------------
# Current user (GET /api/auth/me/)
# -----------------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    user = request.user
    return Response(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": getattr(user, "role", None),
        }
    )


# -----------------------------
# Register API (POST /api/auth/register/)
# -----------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def register_api(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        try:
            # Create user without role (will be set later)
            user = serializer.save()

            # Auto-login after registration
            backend = "django.contrib.auth.backends.ModelBackend"
            user.backend = backend
            login(request, user, backend=backend)

            return Response(
                {
                    "message": "User registered successfully",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "role": getattr(user, "role", None),
                    },
                },
                status=status.HTTP_201_CREATED,
            )
        except IntegrityError as e:
            # Handle database integrity errors (duplicate username/email)
            error_message = str(e).lower()
            if "username" in error_message:
                return Response(
                    {"username": ["This username is already taken."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif "email" in error_message:
                return Response(
                    {"email": ["This email is already registered."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return Response(
                    {"error": "Registration failed. Please try again."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------
# Login API (POST /api/auth/login/)
# Accepts identifier (username or email) + password
# -----------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def login_api(request):
    identifier = request.data.get("identifier")  # can be username or email
    password = request.data.get("password")

    if not identifier or not password:
        return Response(
            {"error": "Username/email and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Try authenticating with username first
    user = authenticate(request, username=identifier, password=password)

    # If that fails, try treating identifier as email
    if user is None:
        try:
            user_obj = User.objects.get(email=identifier)
            user = authenticate(
                request, username=user_obj.username, password=password
            )
        except User.DoesNotExist:
            user = None

    if user is not None and user.is_active:
        login(request, user)
        return Response(
            {
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": getattr(user, "role", None),
                },
            },
            status=status.HTTP_200_OK,
        )

    if user is not None and not user.is_active:
        return Response(
            {"error": "Your account is inactive. Please contact support."},
            status=status.HTTP_403_FORBIDDEN,
        )

    return Response(
        {"error": "Invalid username/email or password."},
        status=status.HTTP_401_UNAUTHORIZED,
    )


# -----------------------------
# Set My Role (POST /api/auth/set-my-role/)
# Self-service role selection (one-time for athlete/coach)
# -----------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def set_my_role(request):
    user = request.user
    role = request.data.get("role")

    # Validate role
    if not role:
        return Response(
            {"error": "Role is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Only allow athlete or coach roles for self-service
    if role not in ["athlete", "coach"]:
        return Response(
            {"error": "Invalid role. Only 'athlete' or 'coach' allowed."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Check if user already has a role set (one-time only)
    if user.role and user.role != "athlete":  # athlete is default, so allow change
        return Response(
            {"error": "Role already set. Contact admin to change."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Set the role
    user.role = role
    user.save()

    return Response(
        {
            "message": "Role set successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            },
        },
        status=status.HTTP_200_OK,
    )


# -----------------------------
# Set Role (POST /api/auth/set-role/)
# Admin-only endpoint to set any user's role
# -----------------------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def set_role(request):
    # Check if user is admin
    if request.user.role != "admin" and not request.user.is_superuser:
        return Response(
            {"error": "Only admins can set user roles."},
            status=status.HTTP_403_FORBIDDEN,
        )

    user_id = request.data.get("user_id")
    role = request.data.get("role")

    if not user_id or not role:
        return Response(
            {"error": "user_id and role are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Validate role
    valid_roles = ["athlete", "coach", "coach_pending", "admin"]
    if role not in valid_roles:
        return Response(
            {"error": f"Invalid role. Must be one of: {', '.join(valid_roles)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(id=user_id)
        user.role = role
        user.save()
        return Response(
            {
                "message": "Role updated successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                },
            },
            status=status.HTTP_200_OK,
        )
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

