# Performance Reminder System

This system automatically sends notifications to athletes who haven't logged their performance in the last 24 hours.

## Features

- Checks all athletes for activity in the last 24 hours
- Sends notification if no performance logs found
- Prevents duplicate notifications (only one per 24 hours)
- Can be triggered manually via API or management command
- Designed to be run as a scheduled task (cron job)

## Usage

### 1. Management Command (Recommended for Cron Jobs)

Run the management command to check and send reminders:

```bash
python manage.py send_performance_reminders
```

### 2. API Endpoint (Admin Only)

Trigger reminders via API:

```bash
POST /api/notifications/send-performance-reminders/
Authorization: Required (Admin role only)
```

Response:
```json
{
  "message": "Successfully sent 5 performance reminders",
  "count": 5
}
```

### 3. Programmatic Usage

Use the utility function in your code:

```python
from api.notification_utils import check_and_send_performance_reminders

# Send reminders to all inactive athletes
count = check_and_send_performance_reminders()
print(f"Sent {count} reminders")
```

## Setting Up Automated Reminders

### Option 1: Cron Job (Linux/Mac)

Add to crontab to run daily at 8 PM:

```bash
0 20 * * * cd /path/to/project && python manage.py send_performance_reminders
```

### Option 2: Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 8:00 PM
4. Action: Start a program
5. Program: `python`
6. Arguments: `manage.py send_performance_reminders`
7. Start in: `C:\path\to\Backend\backend`

### Option 3: Django-Crontab (Python Package)

Install:
```bash
pip install django-crontab
```

Add to settings.py:
```python
INSTALLED_APPS = [
    ...
    'django_crontab',
]

CRONJOBS = [
    ('0 20 * * *', 'django.core.management.call_command', ['send_performance_reminders']),
]
```

Run:
```bash
python manage.py crontab add
```

### Option 4: Celery (For Production)

Create a periodic task:

```python
from celery import shared_task
from api.notification_utils import check_and_send_performance_reminders

@shared_task
def send_daily_performance_reminders():
    return check_and_send_performance_reminders()
```

Configure in celery beat schedule:
```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'send-performance-reminders': {
        'task': 'api.tasks.send_daily_performance_reminders',
        'schedule': crontab(hour=20, minute=0),  # 8 PM daily
    },
}
```

## Notification Details

When an athlete receives a reminder:

- **Type**: `performance_reminder`
- **Title**: "Time to Log Your Performance"
- **Message**: "You haven't logged any performance in the last 24 hours. Keep track of your progress by logging your workouts!"
- **Link**: Points to performance log page

Athletes can view these notifications in their notification center.

## Testing

Test the system manually:

```bash
# Run the command
python manage.py send_performance_reminders

# Or call the API (as admin)
curl -X POST http://localhost:8000/api/notifications/send-performance-reminders/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

## Database Migration

Apply the migration to add the new notification type:

```bash
python manage.py migrate api
```

This adds `performance_reminder` to the notification type choices.
