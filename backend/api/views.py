from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import ensure_csrf_cookie

from .serializers import UserSerializer
from accounts.models import User
from rest_framework.permissions import IsAuthenticated, AllowAny


# -----------------------------
# Current user (after login, incl. Google)
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
            "role": getattr(user, "role", None),
        }
    )


# -----------------------------
# CSRF Endpoint
# -----------------------------
@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([AllowAny])
def get_csrf(request):
    return Response({"message": "CSRF cookie set"})


# -----------------------------
# Register API
# -----------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def register_api(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        login(request, user)
        return Response(
            {
                "message": "User registered successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -----------------------------
# Login API (email or username)
# -----------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def login_api(request):
    identifier = request.data.get("identifier")  # can be username or email
    password = request.data.get("password")

    if not identifier or not password:
        return Response(
            {"error": "Email/username and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Try username first
    user = authenticate(request, username=identifier, password=password)

    # If not found, try treating identifier as email
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
                    "role": getattr(user, "role", None),
                },
            },
            status=status.HTTP_200_OK,
        )

    if user is not None and not user.is_active:
        return Response(
            {"error": "User account is inactive."},
            status=status.HTTP_403_FORBIDDEN,
        )

    return Response(
        {"error": "Invalid credentials"},
        status=status.HTTP_401_UNAUTHORIZED,
    )


# -----------------------------
# Set Role API
# -----------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def set_role(request):
    user_id = request.data.get("user_id")
    role = request.data.get("role")

    if not user_id or not role:
        return Response(
            {"error": "user_id and role are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(id=user_id)
        user.role = role
        user.save()
        return Response(
            {"message": "Role updated successfully"},
            status=status.HTTP_200_OK,
        )
    except User.DoesNotExist:
        return Response(
            {"error": "User not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
