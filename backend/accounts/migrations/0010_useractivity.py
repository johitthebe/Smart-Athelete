# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_athleteprofile'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserActivity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_type', models.CharField(choices=[('user_registered', 'User Registered'), ('user_login', 'User Login'), ('profile_updated', 'Profile Updated'), ('goal_created', 'Goal Created'), ('goal_updated', 'Goal Updated'), ('goal_completed', 'Goal Completed'), ('workout_logged', 'Workout Logged'), ('performance_logged', 'Performance Logged'), ('coach_request_sent', 'Coach Request Sent'), ('coach_request_accepted', 'Coach Request Accepted'), ('coach_request_rejected', 'Coach Request Rejected'), ('coach_approved', 'Coach Approved'), ('coach_rejected', 'Coach Rejected'), ('athlete_assigned', 'Athlete Assigned'), ('feedback_given', 'Feedback Given'), ('password_changed', 'Password Changed'), ('onboarding_completed', 'Onboarding Completed')], max_length=50)),
                ('description', models.TextField()),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'User Activities',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['user', '-created_at'], name='accounts_us_user_id_5e8b9a_idx'),
                    models.Index(fields=['action_type', '-created_at'], name='accounts_us_action__7c4f3e_idx'),
                    models.Index(fields=['-created_at'], name='accounts_us_created_3f2a1b_idx'),
                ],
            },
        ),
    ]
