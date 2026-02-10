from rest_framework import serializers
from .models import Goal, Benchmark, PerformanceLog

class BenchmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benchmark
        fields = ['id', 'event', 'level', 'benchmark_value', 'unit', 'created_at']


class GoalSerializer(serializers.ModelSerializer):
    benchmark = BenchmarkSerializer(read_only=True)
    benchmark_id = serializers.PrimaryKeyRelatedField(
        queryset=Benchmark.objects.all(),
        write_only=True,
        required=False,
        source='benchmark',
    )
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Goal
        fields = [
            'id', 'event', 'target_value', 'current_value',
            'benchmark', 'benchmark_id', 'deadline', 'status',
            'progress', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'athlete', 'current_value', 'created_at', 'updated_at', 'progress',
        ]

    def get_progress(self, obj):
        return {
            'percentage': obj.progress_percentage(),
            'is_completed': obj.status == 'completed',
            'distance_to_target': obj.current_value - obj.target_value,
        }

    def create(self, validated_data):
        validated_data['athlete'] = self.context['request'].user
        return super().create(validated_data)


class PerformanceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceLog
        fields = [
            'id', 'event', 'value', 'intensity',
            'notes', 'date_logged', 'created_at',
        ]
        read_only_fields = ['athlete', 'created_at']

    def create(self, validated_data):
        validated_data['athlete'] = self.context['request'].user
        return super().create(validated_data)
