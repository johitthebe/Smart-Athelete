"""
AI Service for generating personalized goal and workout suggestions
Uses Llama 3 8B via Groq API (cloud-based, super fast!)
"""
import json
from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Avg, Count, Max, Min
from groq import Groq

from .models import PerformanceLog, Goal, ActivityType
from .ai_models import SuggestedGoal, SuggestedWorkout


class AIService:
    """Service for AI-powered suggestions using Groq API with Llama 3 8B"""
    
    MODEL_NAME = "llama-3.1-8b-instant"  # Groq's Llama 3.1 8B model (updated)
    
    @classmethod
    def _get_groq_client(cls):
        """Initialize Groq client with API key from settings"""
        api_key = settings.GROQ_API_KEY
        if not api_key or api_key == 'your-groq-api-key-here':
            raise ValueError(
                "GROQ_API_KEY not configured. "
                "Get your API key from https://console.groq.com and add it to settings.py or environment variables."
            )
        return Groq(api_key=api_key)
    
    @classmethod
    def _call_llama(cls, prompt, system_prompt="You are a professional sports coach AI assistant."):
        """Call Groq API with Llama 3 8B - returns response in ~1 second!"""
        try:
            client = cls._get_groq_client()
            
            response = client.chat.completions.create(
                model=cls.MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2048,
                top_p=0.9,
            )
            
            # Extract response text from Groq response object
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return None
    
    @classmethod
    def _analyze_athlete_data(cls, athlete):
        """
        Analyze athlete's performance history in detail
        This creates UNIQUE data for each athlete that makes AI suggestions personalized
        """
        logs = PerformanceLog.objects.filter(athlete=athlete).order_by('-date')
        
        if not logs.exists():
            return {
                'total_workouts': 0,
                'recent_workouts': [],
                'activity_summary': {},
                'trends': 'No workout history yet',
                'training_frequency': 0,
                'improvement_rate': 0,
                'consistency_score': 0,
            }
        
        # Get recent workouts (last 30 days)
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        recent_logs = logs.filter(date__gte=thirty_days_ago)
        
        # Calculate training frequency (sessions per week)
        if recent_logs.exists():
            days_span = (recent_logs.first().date - recent_logs.last().date).days or 1
            training_frequency = (recent_logs.count() / days_span) * 7
        else:
            training_frequency = 0
        
        # Activity breakdown with detailed stats
        activity_summary = {}
        for log in recent_logs:
            activity = str(log.activity_type) if log.activity_type else log.event
            if activity not in activity_summary:
                activity_summary[activity] = {
                    'count': 0,
                    'total_distance': 0,
                    'total_duration': 0,
                    'avg_intensity': 0,
                    'feelings': [],
                    'best_distance': 0,
                    'avg_distance': 0,
                }
            
            activity_summary[activity]['count'] += 1
            if log.distance:
                activity_summary[activity]['total_distance'] += log.distance
                activity_summary[activity]['best_distance'] = max(
                    activity_summary[activity]['best_distance'], 
                    log.distance
                )
            if log.duration:
                activity_summary[activity]['total_duration'] += log.duration
            activity_summary[activity]['avg_intensity'] += log.perceived_effort
            activity_summary[activity]['feelings'].append(log.how_felt)
        
        # Calculate averages and improvement trends
        for activity in activity_summary:
            count = activity_summary[activity]['count']
            activity_summary[activity]['avg_intensity'] /= count
            if activity_summary[activity]['total_distance'] > 0:
                activity_summary[activity]['avg_distance'] = activity_summary[activity]['total_distance'] / count
        
        # Calculate improvement rate (compare first half vs second half of recent workouts)
        improvement_rate = 0
        if recent_logs.count() >= 4:
            mid_point = recent_logs.count() // 2
            recent_half = list(recent_logs[:mid_point])
            older_half = list(recent_logs[mid_point:mid_point*2])
            
            if recent_half and older_half:
                recent_avg_distance = sum(log.distance or 0 for log in recent_half) / len(recent_half)
                older_avg_distance = sum(log.distance or 0 for log in older_half) / len(older_half)
                
                if older_avg_distance > 0:
                    improvement_rate = ((recent_avg_distance - older_avg_distance) / older_avg_distance) * 100
        
        # Calculate consistency score (how regular are workouts?)
        consistency_score = 0
        if recent_logs.count() >= 3:
            dates = [log.date for log in recent_logs]
            gaps = [(dates[i] - dates[i+1]).days for i in range(len(dates)-1)]
            avg_gap = sum(gaps) / len(gaps) if gaps else 0
            # Lower gap = more consistent (score 0-10)
            consistency_score = max(0, 10 - (avg_gap / 2))
        
        # Recent workout details (last 10-15 workouts for AI context)
        recent_workouts = []
        for log in recent_logs[:15]:  # Last 15 workouts
            recent_workouts.append({
                'date': log.date.isoformat(),
                'activity': str(log.activity_type) if log.activity_type else log.event,
                'distance': log.distance,
                'duration': log.duration,
                'intensity': log.intensity_level,
                'perceived_effort': log.perceived_effort,
                'how_felt': log.how_felt,
                'notes': log.notes[:100] if log.notes else ''  # Truncate long notes
            })
        
        # Get personal bests
        personal_bests = {}
        for activity in activity_summary:
            personal_bests[activity] = activity_summary[activity]['best_distance']
        
        return {
            'total_workouts': logs.count(),
            'recent_workouts_count': recent_logs.count(),
            'recent_workouts': recent_workouts,
            'activity_summary': activity_summary,
            'training_frequency': round(training_frequency, 1),
            'improvement_rate': round(improvement_rate, 1),
            'consistency_score': round(consistency_score, 1),
            'personal_bests': personal_bests,
        }
    
    @classmethod
    def generate_goal_suggestions(cls, athlete):
        """
        Generate 3 UNIQUE goal suggestions per athlete (conservative, recommended, ambitious)
        Uniqueness comes from feeding athlete's SPECIFIC data to AI
        """
        
        # Analyze athlete data - THIS IS UNIQUE PER ATHLETE
        data = cls._analyze_athlete_data(athlete)
        
        if data['total_workouts'] == 0:
            # Beginner suggestions
            return cls._generate_beginner_goals(athlete)
        
        # Get active goals for context
        active_goals = Goal.objects.filter(athlete=athlete, status='active')
        goals_context = []
        for goal in active_goals:
            goals_context.append({
                'name': goal.name,
                'target': f"{goal.target_value}{goal.target_unit}",
                'progress': f"{goal.progress_percentage():.1f}%",
                'deadline': goal.deadline.isoformat()
            })
        
        # Build PERSONALIZED context for AI - THIS MAKES SUGGESTIONS UNIQUE
        context = f"""
Athlete Profile Analysis:
- Total workouts completed: {data['total_workouts']}
- Recent activity (last 30 days): {data['recent_workouts_count']} workouts
- Training frequency: {data['training_frequency']} sessions per week
- Improvement rate: {data['improvement_rate']}% (comparing recent vs older performance)
- Consistency score: {data['consistency_score']}/10
- Personal bests: {json.dumps(data['personal_bests'], indent=2)}

Current Active Goals:
{json.dumps(goals_context, indent=2) if goals_context else "No active goals"}

Activity Breakdown (Last 30 Days):
{json.dumps(data['activity_summary'], indent=2)}

Recent Workout History (Last 15 Sessions):
{json.dumps(data['recent_workouts'], indent=2)}

Based on THIS SPECIFIC ATHLETE'S data, suggest 3 SMART goals for the next 4-8 weeks.
The athlete trains multiple sports - suggest goals across DIFFERENT activities where possible.
Do NOT default to running unless it is the only activity logged.

1. CONSERVATIVE: Safe, achievable goal based on current performance
2. RECOMMENDED: Optimal challenge level considering improvement rate and consistency
3. AMBITIOUS: Stretch goal that pushes limits but remains realistic

For each goal, provide:
- Event/Activity type (match to their logged activities - use variety if they train multiple sports)
- Target value and unit (be specific, use their personal bests as baseline)
- Deadline (in weeks, adjust based on their improvement rate)
- Reasoning (explain WHY this goal fits THIS athlete's data)
- Training required (specific to their current frequency and consistency)
- Key tip (personalized advice based on their patterns)

Format as JSON array with these exact fields:
[
  {{
    "difficulty_level": "conservative",
    "event": "...",
    "target_value": 0.0,
    "unit": "...",
    "deadline_weeks": 0,
    "reasoning": "...",
    "training_required": "...",
    "key_tip": "..."
  }},
  {{
    "difficulty_level": "recommended",
    "event": "...",
    "target_value": 0.0,
    "unit": "...",
    "deadline_weeks": 0,
    "reasoning": "...",
    "training_required": "...",
    "key_tip": "..."
  }},
  {{
    "difficulty_level": "ambitious",
    "event": "...",
    "target_value": 0.0,
    "unit": "...",
    "deadline_weeks": 0,
    "reasoning": "...",
    "training_required": "...",
    "key_tip": "..."
  }}
]

Return ONLY the JSON array, no other text.
"""
        
        system_prompt = """You are an expert sports coach AI. Analyze each athlete's UNIQUE data and suggest PERSONALIZED, achievable goals.
Consider their specific training frequency, improvement rate, consistency, and how they felt during workouts.
Be encouraging but realistic. Goals should be SMART (Specific, Measurable, Achievable, Relevant, Time-bound).
Different athletes get DIFFERENT suggestions based on THEIR data - a consistent 4x/week trainer gets more ambitious goals than a 1x/week beginner."""
        
        response = cls._call_llama(context, system_prompt)
        
        if not response:
            return cls._generate_fallback_goals(athlete, data)
        
        # Parse AI response
        try:
            # Extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                suggestions_data = json.loads(response[json_start:json_end])
                
                # Create SuggestedGoal objects
                suggestions = []
                for suggestion in suggestions_data[:3]:  # Max 3
                    suggested_goal = SuggestedGoal.objects.create(
                        athlete=athlete,
                        event=suggestion.get('event', 'Running'),
                        target_value=suggestion.get('target_value', 5.0),
                        unit=suggestion.get('unit', 'km'),
                        deadline_weeks=suggestion.get('deadline_weeks', 4),
                        difficulty_level=suggestion.get('difficulty_level', suggestion.get('difficulty', 'recommended')),
                        reasoning=suggestion.get('reasoning', ''),
                        training_required=suggestion.get('training_required', ''),
                        key_tip=suggestion.get('key_tip', '')
                    )
                    suggestions.append(suggested_goal)
                
                return suggestions
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing AI response: {e}")
            return cls._generate_fallback_goals(athlete, data)
    
    @classmethod
    def _generate_beginner_goals(cls, athlete):
        """Generate beginner-friendly goals for new athletes"""
        goals_data = [
            {
                'difficulty_level': 'conservative',
                'event': 'Cardio',
                'target_value': 10.0,
                'unit': 'km',
                'deadline_weeks': 4,
                'reasoning': 'Start with a manageable distance goal to build consistency and confidence',
                'training_required': '3 sessions per week, gradually increasing distance by 10% each week',
                'key_tip': 'Focus on completing the distance, not speed. Walk breaks are perfectly fine!'
            },
            {
                'difficulty_level': 'recommended',
                'event': 'Endurance',
                'target_value': 30.0,
                'unit': 'minutes',
                'deadline_weeks': 6,
                'reasoning': 'Build endurance with a moderate challenge that establishes a solid base',
                'training_required': '3-4 sessions per week with one longer session on weekends',
                'key_tip': 'Include rest days for recovery - your body gets stronger during rest, not during workouts'
            },
            {
                'difficulty_level': 'ambitious',
                'event': 'Fitness',
                'target_value': 5.0,
                'unit': 'sessions/week',
                'deadline_weeks': 8,
                'reasoning': 'Build a consistent training habit across any activity you enjoy',
                'training_required': 'Gradually increase from 3 to 5 sessions per week over 8 weeks',
                'key_tip': 'Pick activities you enjoy — consistency matters more than the specific sport'
            }
        ]
        
        suggestions = []
        for goal_data in goals_data:
            suggested_goal = SuggestedGoal.objects.create(
                athlete=athlete,
                **goal_data
            )
            suggestions.append(suggested_goal)
        
        return suggestions
    
    @classmethod
    def _generate_fallback_goals(cls, athlete, data):
        """Generate fallback goals using heuristics if AI fails"""
        activity_summary = data.get('activity_summary', {})
        
        if not activity_summary:
            return cls._generate_beginner_goals(athlete)
        
        # Find most common activity
        most_common = max(activity_summary.items(), key=lambda x: x[1]['count'])
        activity_name = most_common[0]
        stats = most_common[1]
        
        avg_distance = stats['avg_distance'] if stats['avg_distance'] > 0 else 5.0
        improvement_rate = data.get('improvement_rate', 0)
        training_freq = data.get('training_frequency', 3)
        
        # Adjust targets based on improvement rate and frequency
        conservative_multiplier = 1.15 if improvement_rate > 5 else 1.1
        recommended_multiplier = 1.4 if improvement_rate > 5 else 1.3
        ambitious_multiplier = 2.0 if improvement_rate > 10 else 1.8
        
        goals_data = [
            {
                'difficulty_level': 'conservative',
                'event': activity_name,
                'target_value': round(avg_distance * conservative_multiplier, 1),
                'unit': 'km',
                'deadline_weeks': 4,
                'reasoning': f'Increase your average {activity_name} distance by {int((conservative_multiplier-1)*100)}% based on current performance',
                'training_required': f'Maintain {int(training_freq)} sessions per week, slightly increase distance',
                'key_tip': 'Gradual progression prevents injury and builds sustainable habits'
            },
            {
                'difficulty_level': 'recommended',
                'event': activity_name,
                'target_value': round(avg_distance * recommended_multiplier, 1),
                'unit': 'km',
                'deadline_weeks': 6,
                'reasoning': f'Challenge yourself with {int((recommended_multiplier-1)*100)}% more {activity_name} volume',
                'training_required': f'Increase to {int(training_freq)+1} sessions per week with varied intensity',
                'key_tip': 'Mix easy and hard training days - not every workout should be maximum effort'
            },
            {
                'difficulty_level': 'ambitious',
                'event': activity_name,
                'target_value': round(avg_distance * ambitious_multiplier, 1),
                'unit': 'km',
                'deadline_weeks': 8,
                'reasoning': f'Significantly expand your {activity_name} capacity with {int((ambitious_multiplier-1)*100)}% increase',
                'training_required': 'Structured training plan with progressive overload and recovery weeks',
                'key_tip': 'Prioritize recovery, nutrition, and sleep - these are as important as training'
            }
        ]
        
        suggestions = []
        for goal_data in goals_data:
            suggested_goal = SuggestedGoal.objects.create(
                athlete=athlete,
                **goal_data
            )
            suggestions.append(suggested_goal)
        
        return suggestions
    
    @classmethod
    def generate_workout_suggestions(cls, athlete):
        """
        Generate personalized workout suggestions
        Uniqueness comes from athlete's specific training patterns and goals
        """
        
        # Analyze athlete data - UNIQUE PER ATHLETE
        data = cls._analyze_athlete_data(athlete)
        
        if data['total_workouts'] == 0:
            return cls._generate_beginner_workouts(athlete)
        
        # Get active goals for context
        active_goals = Goal.objects.filter(athlete=athlete, status='active')
        goals_context = []
        for goal in active_goals:
            goals_context.append({
                'name': goal.name,
                'target': f"{goal.target_value}{goal.target_unit}",
                'progress': f"{goal.progress_percentage():.1f}%",
                'deadline': goal.deadline.isoformat()
            })
        
        # Build PERSONALIZED context for AI
        context = f"""
Athlete Profile Analysis:
- Total workouts: {data['total_workouts']}
- Recent activity (last 30 days): {data['recent_workouts_count']} workouts
- Training frequency: {data['training_frequency']} sessions per week
- Improvement rate: {data['improvement_rate']}%
- Consistency score: {data['consistency_score']}/10

Active Goals:
{json.dumps(goals_context, indent=2) if goals_context else "No active goals"}

Recent Workout History (Last 10 Sessions):
{json.dumps(data['recent_workouts'][:10], indent=2)}

Activity Summary:
{json.dumps(data['activity_summary'], indent=2)}

Based on THIS ATHLETE'S specific data, suggest 3 workouts for this week:
1. One RECOVERY workout (easy, restorative) - especially if recent workouts show "tired" or "struggled"
2. One ENDURANCE workout (steady, moderate) - build aerobic base
3. One INTENSITY workout (challenging, high effort) - improve performance

IMPORTANT: Tailor workouts to THIS athlete's:
- Current training frequency ({data['training_frequency']} sessions/week)
- Recent feelings (check how_felt in recent workouts)
- Active goals (help them progress toward goals)
- Improvement trend ({data['improvement_rate']}%)

For each workout, provide:
- Workout type (recovery/endurance/intervals/speed)
- Name (catchy, motivating, specific to their activity)
- Description (detailed instructions they can follow)
- Target value and unit (realistic based on their recent performance)
- Intensity level (easy/moderate/hard/race)
- Estimated duration (minutes, realistic for their fitness level)
- Reasoning (why THIS workout for THIS athlete NOW)
- Benefit (what it improves specifically for them)

Format as JSON array:
[
  {{
    "workout_type": "recovery",
    "name": "...",
    "description": "...",
    "target_value": 0.0,
    "target_unit": "km",
    "intensity": "easy",
    "estimated_duration": 30,
    "reasoning": "...",
    "benefit": "..."
  }},
  {{
    "workout_type": "endurance",
    "name": "...",
    "description": "...",
    "target_value": 0.0,
    "target_unit": "km",
    "intensity": "moderate",
    "estimated_duration": 45,
    "reasoning": "...",
    "benefit": "..."
  }},
  {{
    "workout_type": "intervals",
    "name": "...",
    "description": "...",
    "target_value": 0.0,
    "target_unit": "km",
    "intensity": "hard",
    "estimated_duration": 40,
    "reasoning": "...",
    "benefit": "..."
  }}
]

Return ONLY the JSON array, no other text.
"""
        
        system_prompt = """You are an expert sports coach AI. Design PERSONALIZED workouts based on each athlete's UNIQUE history and goals.
Consider their recent performance, how they felt, their active goals, and training frequency.
Workouts should be varied, progressive, and include proper recovery.
Different athletes get DIFFERENT workouts - a tired athlete needs recovery, a fresh athlete can handle intensity."""
        
        response = cls._call_llama(context, system_prompt)
        
        if not response:
            return cls._generate_fallback_workouts(athlete, data)
        
        # Parse AI response
        try:
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                workouts_data = json.loads(response[json_start:json_end])
                
                suggestions = []
                for workout in workouts_data[:3]:
                    suggested_workout = SuggestedWorkout.objects.create(
                        athlete=athlete,
                        workout_type=workout.get('workout_type', 'endurance'),
                        name=workout.get('name', 'Workout'),
                        description=workout.get('description', ''),
                        target_value=workout.get('target_value', 5.0),
                        target_unit=workout.get('target_unit', 'km'),
                        intensity=workout.get('intensity', 'moderate'),
                        estimated_duration=workout.get('estimated_duration', 30),
                        reasoning=workout.get('reasoning', ''),
                        benefit=workout.get('benefit', '')
                    )
                    suggestions.append(suggested_workout)
                
                return suggestions
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing AI response: {e}")
            return cls._generate_fallback_workouts(athlete, data)
    
    @classmethod
    def _generate_beginner_workouts(cls, athlete):
        """Generate beginner-friendly workouts"""
        workouts_data = [
            {
                'workout_type': 'recovery',
                'name': 'Easy Movement Session',
                'description': 'Choose any low-intensity activity (walk, light jog, cycling, swimming). Focus on enjoying the movement, not speed. You should be able to hold a conversation throughout.',
                'target_value': 20.0,
                'target_unit': 'minutes',
                'intensity': 'easy',
                'estimated_duration': 20,
                'reasoning': 'Build base fitness with low-stress activity that your body can handle easily',
                'benefit': 'Improves cardiovascular health and builds the habit of regular exercise'
            },
            {
                'workout_type': 'endurance',
                'name': 'Steady Aerobic Builder',
                'description': 'Pick your preferred activity (running, cycling, swimming, rowing) and maintain a steady conversational pace for 30 minutes.',
                'target_value': 30.0,
                'target_unit': 'minutes',
                'intensity': 'moderate',
                'estimated_duration': 30,
                'reasoning': 'Develop aerobic capacity which is the foundation of all endurance sports',
                'benefit': 'Builds endurance, stamina, and teaches your body to use fat for fuel'
            },
            {
                'workout_type': 'intervals',
                'name': 'Intro to Intensity',
                'description': '5 min warmup, then 5 rounds of (2 min faster pace, 2 min easy recovery), finish with 5 min cooldown. Works for any cardio activity.',
                'target_value': 25.0,
                'target_unit': 'minutes',
                'intensity': 'hard',
                'estimated_duration': 25,
                'reasoning': 'Introduce intensity safely with equal work-to-rest ratio',
                'benefit': 'Improves cardiovascular fitness and teaches your body to handle higher intensities'
            }
        ]
        
        suggestions = []
        for workout_data in workouts_data:
            suggested_workout = SuggestedWorkout.objects.create(
                athlete=athlete,
                **workout_data
            )
            suggestions.append(suggested_workout)
        
        return suggestions
    
    @classmethod
    def _generate_fallback_workouts(cls, athlete, data):
        """Generate fallback workouts using heuristics if AI fails"""
        recent_workouts = data.get('recent_workouts', [])
        
        if not recent_workouts:
            return cls._generate_beginner_workouts(athlete)
        
        # Analyze recent intensity and feelings
        recent_efforts = [w.get('perceived_effort', 5) for w in recent_workouts[:3]]
        avg_effort = sum(recent_efforts) / len(recent_efforts) if recent_efforts else 5
        
        recent_feelings = [w.get('how_felt', 'okay') for w in recent_workouts[:3]]
        feeling_tired = recent_feelings.count('tired') + recent_feelings.count('struggled')
        
        # Adjust workout intensity based on recent fatigue
        if feeling_tired >= 2 or avg_effort >= 8:
            recovery_emphasis = True
        else:
            recovery_emphasis = False
        
        avg_distance = 5.0
        if data.get('activity_summary'):
            most_common = max(data['activity_summary'].items(), key=lambda x: x[1]['count'])
            avg_distance = most_common[1].get('avg_distance', 5.0) or 5.0
        
        workouts_data = [
            {
                'workout_type': 'recovery',
                'name': 'Active Recovery Run' if not recovery_emphasis else 'Essential Recovery - Take It Easy',
                'description': 'Easy-paced run to promote recovery. Keep heart rate low, focus on form. Walk breaks encouraged.',
                'target_value': round(avg_distance * 0.6, 1),
                'target_unit': 'km',
                'intensity': 'easy',
                'estimated_duration': 25,
                'reasoning': 'Recovery from recent training load' + (' - you need this!' if recovery_emphasis else ''),
                'benefit': 'Promotes blood flow, aids recovery, maintains fitness without adding stress'
            },
            {
                'workout_type': 'endurance',
                'name': 'Steady Distance Run',
                'description': 'Maintain a comfortable, steady pace throughout. Conversational effort level.',
                'target_value': round(avg_distance * 1.2, 1),
                'target_unit': 'km',
                'intensity': 'moderate',
                'estimated_duration': 40,
                'reasoning': 'Build aerobic base and endurance capacity',
                'benefit': 'Improves endurance, fat burning, and cardiovascular efficiency'
            },
            {
                'workout_type': 'intervals',
                'name': 'Tempo Intervals' if not recovery_emphasis else 'Light Fartlek (Skip if tired)',
                'description': 'Warmup 10min, then 4 rounds of (5min comfortably hard, 2min easy), cooldown 10min',
                'target_value': round(avg_distance * 1.4, 1),
                'target_unit': 'km',
                'intensity': 'hard',
                'estimated_duration': 45,
                'reasoning': 'Improve lactate threshold and speed' + (' - only if feeling fresh' if recovery_emphasis else ''),
                'benefit': 'Increases speed, stamina, and ability to sustain faster paces'
            }
        ]
        
        suggestions = []
        for workout_data in workouts_data:
            suggested_workout = SuggestedWorkout.objects.create(
                athlete=athlete,
                **workout_data
            )
            suggestions.append(suggested_workout)
        
        return suggestions
