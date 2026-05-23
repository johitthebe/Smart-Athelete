#!/bin/bash
# Shell script to send performance reminders
# Run this script daily using cron

cd "$(dirname "$0")/backend"
python manage.py send_performance_reminders
