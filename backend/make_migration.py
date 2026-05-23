#!/usr/bin/env python
"""Script to create migration without interactive prompts"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.core.management import call_command

# Mock input to always return 'n'
original_input = __builtins__.input
__builtins__.input = lambda *args: 'n'

try:
    call_command('makemigrations', 'accounts', interactive=False)
finally:
    __builtins__.input = original_input
