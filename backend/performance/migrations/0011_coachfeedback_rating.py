# Generated migration for adding rating field to CoachFeedback

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('performance', '0010_coachfeedback_acknowledged_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='coachfeedback',
            name='rating',
            field=models.IntegerField(blank=True, help_text="Athlete's rating of the feedback (1-5 stars)", null=True),
        ),
    ]
