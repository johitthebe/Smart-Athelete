from django.contrib import admin
from .models import AdminNotification


@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "notification_type", "coach", "is_read", "created_at")
    search_fields = ("coach__username", "coach__email", "message")
    list_filter = ("notification_type", "is_read", "created_at")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)
