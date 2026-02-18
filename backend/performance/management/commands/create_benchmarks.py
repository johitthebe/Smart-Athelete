"""
Management command to create famous athlete benchmarks
Usage: python manage.py create_benchmarks
"""
from django.core.management.base import BaseCommand
from performance.models import Benchmark


class Command(BaseCommand):
    help = 'Create famous athlete benchmarks for various sports'

    def handle(self, *args, **kwargs):
        benchmarks = [
            # Track & Field - Sprints
            {
                'benchmark_type': 'athlete',
                'athlete_name': 'Usain Bolt',
                'event': '100m Sprint',
                'level': 'World Record',
                'benchmark_value': 9.58,
                'unit': 'seconds',
                'description': 'Set at 2009 World Championships in Berlin'
            },
            {
                'benchmark_type': 'athlete',
                'athlete_name': 'Usain Bolt',
                'event': '200m Sprint',
                'level': 'World Record',
                'benchmark_value': 19.19,
                'unit': 'seconds',
                'description': 'Set at 2009 World Championships in Berlin'
            },
            {
                'benchmark_type': 'athlete',
                'athlete_name': 'Florence Griffith-Joyner',
                'event': '100m Sprint',
                'level': 'World Record (Women)',
                'benchmark_value': 10.49,
                'unit': 'seconds',
                'description': 'Set in 1988 at US Olympic Trials'
            },
            {
                'benchmark_type': 'athlete',
                'athlete_name': 'Wayde van Niekerk',
                'event': '400m Sprint',
                'level': 'World Record',
                'benchmark_value': 43.03,
                'unit': 'seconds',
                'description': 'Set at 2016 Rio Olympics'
            },
            
            # Track & Field - Distance
            {
                'benchmark_type': 'athlete',
                'athlete_name': 'Eliud Kipchoge',
                'event': 'Marathon',
                'level': 'World Record',
                'benchmark_value': 2.0139,
                'unit': 'hours',
                'description': '2:01:39 at 2018 Berlin Marathon'
            },
            {
                'benchmark_type': 'athlete',
                'athlete_name': 'Eliud Kipchoge',
                'event': 'Marathon',
                'level': 'Sub-2 Hour (Unofficial)',
                'benchmark_value': 1.5940,
                'unit': 'hours',
                'description': '1:59:40 at INEOS 1:59 Challenge 2019'
            },
            {
                'benchmark_type': 'athlete',
                'athlete_name': 'Joshua Cheptegei',
                'event': '5000m',
                'level': 'World Record',
                'benchmark_value': 12.35,
                'unit': 'minutes',
                'description': 'Set in 2020 in Monaco'
            },
            {
                'benchmark_type': 'athlete',
                'athlete_name': 'Joshua Cheptegei',
                'event': '10000m',
                'level': 'World Record',
                'benchmark_value': 26.11,
                'unit': 'minutes',
                'description': 'Set in 2020 in Valencia'
            },
            
            # Swimming
            {
                'benchmark_type': 'athlete',
                'athlete_name': 'Michael Phelps',
                'event': '100m Butterfly',
                'level': 'Olympic Record',
                'benchmark_value': 50.58,
                'unit': 'seconds',
                'description': 'Set at 2008 Beijing Olympics'
            },
            {
                'benchmark_type': 'athlete',
                'athlete_name': 'Caeleb Dressel',
                'event': '100m Freestyle',
                'level': 'World Record',
                'benchmark_value': 46.96,
                'unit': 'seconds',
                'description': 'Set at 2019 World Championships'
            },
            {
                'benchmark_type': 'athlete',
                'athlete_name': 'Katie Ledecky',
                'event': '1500m Freestyle',
                'level': 'World Record (Women)',
                'benchmark_value': 15.2,
                'unit': 'minutes',
                'description': 'Set at 2018 Pan Pacific Championships'
            },
            
            # Cycling
            {
                'benchmark_type': 'athlete',
                'athlete_name': 'Victor Campenaerts',
                'event': 'Hour Record (Cycling)',
                'level': 'World Record',
                'benchmark_value': 55.089,
                'unit': 'km',
                'description': 'Set in 2019 in Aguascalientes, Mexico'
            },
            
            # High Jump
            {
                'benchmark_type': 'athlete',
                'athlete_name': 'Javier Sotomayor',
                'event': 'High Jump',
                'level': 'World Record',
                'benchmark_value': 2.45,
                'unit': 'meters',
                'description': 'Set in 1993 in Salamanca, Spain'
            },
            
            # Long Jump
            {
                'benchmark_type': 'athlete',
                'athlete_name': 'Mike Powell',
                'event': 'Long Jump',
                'level': 'World Record',
                'benchmark_value': 8.95,
                'unit': 'meters',
                'description': 'Set in 1991 at World Championships in Tokyo'
            },
            
            # General Standards (Non-athlete specific)
            {
                'benchmark_type': 'general',
                'athlete_name': None,
                'event': '5K Run',
                'level': 'Elite',
                'benchmark_value': 15.0,
                'unit': 'minutes',
                'description': 'Elite level 5K time'
            },
            {
                'benchmark_type': 'general',
                'athlete_name': None,
                'event': '5K Run',
                'level': 'Advanced',
                'benchmark_value': 20.0,
                'unit': 'minutes',
                'description': 'Advanced level 5K time'
            },
            {
                'benchmark_type': 'general',
                'athlete_name': None,
                'event': '5K Run',
                'level': 'Intermediate',
                'benchmark_value': 25.0,
                'unit': 'minutes',
                'description': 'Intermediate level 5K time'
            },
            {
                'benchmark_type': 'general',
                'athlete_name': None,
                'event': '5K Run',
                'level': 'Beginner',
                'benchmark_value': 30.0,
                'unit': 'minutes',
                'description': 'Beginner level 5K time'
            },
            {
                'benchmark_type': 'general',
                'athlete_name': None,
                'event': 'Half Marathon',
                'level': 'Elite',
                'benchmark_value': 1.0,
                'unit': 'hours',
                'description': 'Elite level half marathon time'
            },
            {
                'benchmark_type': 'general',
                'athlete_name': None,
                'event': 'Half Marathon',
                'level': 'Advanced',
                'benchmark_value': 1.5,
                'unit': 'hours',
                'description': 'Advanced level half marathon time'
            },
        ]

        created_count = 0
        updated_count = 0

        for benchmark_data in benchmarks:
            benchmark, created = Benchmark.objects.update_or_create(
                benchmark_type=benchmark_data['benchmark_type'],
                event=benchmark_data['event'],
                level=benchmark_data['level'],
                defaults={
                    'athlete_name': benchmark_data['athlete_name'],
                    'benchmark_value': benchmark_data['benchmark_value'],
                    'unit': benchmark_data['unit'],
                    'description': benchmark_data['description'],
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created: {benchmark_data.get("athlete_name", "General")} - '
                        f'{benchmark_data["event"]} ({benchmark_data["level"]})'
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'Updated: {benchmark_data.get("athlete_name", "General")} - '
                        f'{benchmark_data["event"]} ({benchmark_data["level"]})'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary: {created_count} created, {updated_count} updated'
            )
        )
