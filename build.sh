#!/usr/bin/env bash
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Navigate to Django project directory
cd backend

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate --no-input
