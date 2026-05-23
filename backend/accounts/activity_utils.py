from .activity_models import UserActivity


def log_activity(user, action_type, description, metadata=None, request=None):
    """Helper function to log user activities"""
    ip_address = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
    
    return UserActivity.objects.create(
        user=user,
        action_type=action_type,
        description=description,
        metadata=metadata or {},
        ip_address=ip_address
    )
