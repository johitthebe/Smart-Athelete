# Generated manually to add email unique constraint

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_user_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(
                error_messages={'unique': 'This email is already registered.'},
                max_length=254,
                unique=True
            ),
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.UniqueConstraint(fields=['email'], name='unique_email'),
        ),
    ]
