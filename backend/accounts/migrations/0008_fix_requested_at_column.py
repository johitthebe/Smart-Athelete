# Manual migration to fix the requested_at column

from django.db import migrations


def rename_column_if_exists(apps, schema_editor):
    """Rename created_at to requested_at if it exists"""
    with schema_editor.connection.cursor() as cursor:
        # Check if created_at column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='accounts_coachrequest' 
            AND column_name='created_at';
        """)
        
        if cursor.fetchone():
            # Column exists, rename it
            cursor.execute("""
                ALTER TABLE accounts_coachrequest 
                RENAME COLUMN created_at TO requested_at;
            """)
            print("Renamed created_at to requested_at")
        else:
            print("Column created_at does not exist, skipping rename")


def reverse_rename(apps, schema_editor):
    """Reverse the rename"""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            ALTER TABLE accounts_coachrequest 
            RENAME COLUMN requested_at TO created_at;
        """)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_coachcapacitylog_coachrequest_and_more'),
    ]

    operations = [
        migrations.RunPython(rename_column_if_exists, reverse_rename),
    ]
