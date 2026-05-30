# Generated migration for EmailVerificationOTP model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_alter_coachrequest_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailVerificationOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('otp_code', models.CharField(max_length=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('is_used', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='verification_otps', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='emailverificationotp',
            index=models.Index(fields=['user', 'is_used'], name='accounts_ema_user_id_b8c9e5_idx'),
        ),
        migrations.AddIndex(
            model_name='emailverificationotp',
            index=models.Index(fields=['otp_code', 'expires_at'], name='accounts_ema_otp_cod_a1f2d3_idx'),
        ),
    ]
