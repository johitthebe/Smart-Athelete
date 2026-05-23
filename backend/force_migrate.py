#!/usr/bin/env python
"""Force migration without prompts"""
import os
import sys
import django
from unittest.mock import patch

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.core.management import call_command

# Patch input to always return 'n'
with patch('builtins.input', return_value='n'):
    try:
        call_command('migrate', verbosity=2)
        print("\n✓ Migration completed successfully")
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)
