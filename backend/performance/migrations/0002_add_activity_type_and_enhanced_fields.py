# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('performance', '0001_initial'),
    ]

    operations = [
        # Create ActivityType model
        migrations.CreateModel(
            name='ActivityType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('icon', models.CharField(default='🏃', max_length=10)),
                ('requires_distance', models.BooleanField(default=True)),
                ('requires_duration', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        # Add new fields to Goal
        migrations.AddField(
            model_name='goal',
            name='name',
            field=models.CharField(default='Untitled Goal', max_length=200, help_text="Goal name, e.g., 'Run 5km in under 30 minutes'"),
        ),
        migrations.AddField(
            model_name='goal',
            name='description',
            field=models.TextField(blank=True, help_text='Detailed description of the goal'),
        ),
        migrations.AddField(
            model_name='goal',
            name='activity_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='goals', to='performance.activitytype'),
        ),
        migrations.AddField(
            model_name='goal',
            name='target_metric',
            field=models.CharField(
                choices=[('distance', 'Distance'), ('duration', 'Duration'), ('calories', 'Calories'), ('pace', 'Pace')],
                default='distance',
                help_text='Primary metric to track',
                max_length=50
            ),
        ),
        migrations.AddField(
            model_name='goal',
            name='target_unit',
            field=models.CharField(default='km', help_text='Unit of measurement', max_length=20),
        ),
        # Modify Goal.event to be optional
        migrations.AlterField(
            model_name='goal',
            name='event',
            field=models.CharField(blank=True, help_text='e.g., 40m Sprint', max_length=100),
        ),
        # Add new fields to PerformanceLog
        migrations.AddField(
            model_name='performancelog',
            name='goal',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='performance.goal', help_text='Associated goal for this performance log'),
        ),
        migrations.AddField(
            model_name='performancelog',
            name='activity_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='logs', to='performance.activitytype'),
        ),
        migrations.AddField(
            model_name='performancelog',
            name='date',
            field=models.DateField(default='2026-02-15', help_text='Date of the activity'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='performancelog',
            name='duration',
            field=models.IntegerField(blank=True, null=True, help_text='Duration in seconds'),
        ),
        migrations.AddField(
            model_name='performancelog',
            name='distance',
            field=models.FloatField(blank=True, null=True, help_text='Distance in kilometers'),
        ),
        migrations.AddField(
            model_name='performancelog',
            name='heart_rate',
            field=models.IntegerField(blank=True, null=True, help_text='Average heart rate in BPM'),
        ),
        migrations.AddField(
            model_name='performancelog',
            name='calories',
            field=models.IntegerField(blank=True, null=True, help_text='Calories burned'),
        ),
        migrations.AddField(
            model_name='performancelog',
            name='power',
            field=models.IntegerField(blank=True, null=True, help_text='Average power in watts'),
        ),
        migrations.AddField(
            model_name='performancelog',
            name='pace',
            field=models.FloatField(blank=True, null=True, help_text='Pace in min/km'),
        ),
        migrations.AddField(
            model_name='performancelog',
            name='elevation',
            field=models.IntegerField(blank=True, null=True, help_text='Elevation gain in meters'),
        ),
        # Modify PerformanceLog.event and value to be optional
        migrations.AlterField(
            model_name='performancelog',
            name='event',
            field=models.CharField(blank=True, help_text='e.g., 40m Sprint', max_length=100),
        ),
        migrations.AlterField(
            model_name='performancelog',
            name='value',
            field=models.FloatField(blank=True, null=True, help_text='e.g., 4.9 seconds'),
        ),
        # Add indexes
        migrations.AddIndex(
            model_name='goal',
            index=models.Index(fields=['athlete', 'status'], name='performance_athlete_status_idx'),
        ),
        migrations.AddIndex(
            model_name='goal',
            index=models.Index(fields=['deadline'], name='performance_deadline_idx'),
        ),
        migrations.AddIndex(
            model_name='performancelog',
            index=models.Index(fields=['athlete', 'date'], name='performance_athlete_date_idx'),
        ),
        migrations.AddIndex(
            model_name='performancelog',
            index=models.Index(fields=['goal'], name='performance_goal_idx'),
        ),
        migrations.AddIndex(
            model_name='performancelog',
            index=models.Index(fields=['activity_type'], name='performance_activity_type_idx'),
        ),
    ]
