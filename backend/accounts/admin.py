# accounts/admin.py

from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import CoachCredential, CoachApproval, CoachAthleteAssignment
from .activity_models import UserActivity

User = get_user_model()

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "role", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email")
    list_filter = ("role", "is_staff", "is_active")


@admin.register(CoachCredential)
class CoachCredentialAdmin(admin.ModelAdmin):
    list_display = ("id", "coach", "credential_name", "credential_type", "issuing_organization", "issue_date", "uploaded_at")
    search_fields = ("coach__username", "coach__email", "credential_name", "issuing_organization")
    list_filter = ("credential_type", "uploaded_at")
    date_hierarchy = "uploaded_at"


@admin.register(CoachApproval)
class CoachApprovalAdmin(admin.ModelAdmin):
    list_display = ("id", "coach", "status", "reviewed_by", "reviewed_at", "created_at")
    search_fields = ("coach__username", "coach__email")
    list_filter = ("status", "created_at", "reviewed_at")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")


@admin.register(CoachAthleteAssignment)
class CoachAthleteAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "coach", "athlete", "assigned_by", "assigned_at", "is_active")
    search_fields = ("coach__username", "coach__email", "athlete__username", "athlete__email")
    list_filter = ("is_active", "assigned_at")
    date_hierarchy = "assigned_at"
    readonly_fields = ("assigned_at",)


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "action_type", "description", "created_at")
    search_fields = ("user__username", "user__email", "description")
    list_filter = ("action_type", "created_at")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
