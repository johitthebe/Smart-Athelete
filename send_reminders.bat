@echo off
REM Batch script to send performance reminders
REM Run this script daily using Windows Task Scheduler

cd backend
python manage.py send_performance_reminders
pause
