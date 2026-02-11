import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from accounts.models import User

# List all users
print("\n=== All Users ===")
users = User.objects.all()
for u in users:
    print(f"ID: {u.id}, Username: {u.username}, Email: {u.email}, Role: {u.role}")

# Get the first user (or change this to your username)
print("\n=== Setting first user as admin ===")
if users.exists():
    user = users.first()
    print(f"Setting {user.username} as admin...")
    user.role = 'admin'
    user.save()
    print(f"✓ {user.username} is now an admin!")
    print(f"  ID: {user.id}")
    print(f"  Username: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  Role: {user.role}")
else:
    print("No users found!")
