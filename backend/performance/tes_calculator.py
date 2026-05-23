"""
Training Effectiveness Score (TES) Calculator
Pure calculation-based analysis without AI
"""
from datetime import datetime, timedelta
from collections import defaultdict
from django.db.models import Avg, Count, Q


class TESCalculator:
    """Calculate Training Effectiveness Score and generate insights"""
    
    # Weights for overall TES
    CONSISTENCY_WEIGHT = 0.30
    RECOVERY_WEIGHT = 0.30
    GOAL_PROGRESS_WEIGHT = 0.40
    
    @classmethod
    def calculate_tes(cls, athlete):
        """
        Calculate comprehensive Training Effectiveness Score
        Returns dict with scores, analysis, and recommendations
        """
        from performance.models import PerformanceLog, Goal
        
        # Get data for last 30 days
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        logs = PerformanceLog.objects.filter(
            athlete=athlete,
            date__gte=thirty_days_ago
        ).order_by('-date')
        
        if not logs.exists():
            return cls._generate_no_data_response()
        
        # Calculate component scores
        consistency_data = cls._calculate_consistency(logs)
        recovery_data = cls._calculate_recovery(logs)
        goal_data = cls._calculate_goal_progress(athlete)
        
        # Calculate overall TES
        overall_score = (
            consistency_data['score'] * cls.CONSISTENCY_WEIGHT +
            recovery_data['score'] * cls.RECOVERY_WEIGHT +
            goal_data['score'] * cls.GOAL_PROGRESS_WEIGHT
        )
        
        # Analyze root causes
        root_cause = cls._analyze_root_cause(consistency_data, recovery_data, goal_data)
        
        # Generate solution plan
        solution_plan = cls._generate_solution_plan(consistency_data, recovery_data, goal_data)
        
        # Generate coach feedback
        coach_feedback = cls._generate_coach_feedback(
            athlete, consistency_data, recovery_data, goal_data, root_cause, solution_plan
        )
        
        return {
            'overall_score': round(overall_score),
            'status': cls._get_status(overall_score),
            'consistency': consistency_data,
            'recovery': recovery_data,
            'goal_progress': goal_data,
            'root_cause': root_cause,
            'solution_plan': solution_plan,
            'coach_feedback': coach_feedback,
            'predictions': cls._calculate_predictions(overall_score, consistency_data, recovery_data, goal_data)
        }
    
    @classmethod
    def _calculate_consistency(cls, logs):
        """Calculate consistency score and patterns"""
        total_days = 30
        expected_workouts = 12  # ~3-4 per week is reasonable
        actual_workouts = logs.count()
        
        # Calculate completion rate
        completion_rate = min(100, (actual_workouts / expected_workouts) * 100)
        
        # Analyze day-of-week patterns
        day_counts = defaultdict(int)
        day_totals = defaultdict(int)
        
        for log in logs:
            day_name = log.date.strftime('%A')
            day_counts[day_name] += 1
        
        # Calculate expected per day (4 weeks)
        weeks = 4
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            day_totals[day] = weeks
        
        # Find problem days
        problem_days = []
        for day, expected in day_totals.items():
            actual = day_counts.get(day, 0)
            if actual < expected * 0.5:  # Missing more than 50%
                problem_days.append({
                    'day': day,
                    'completed': actual,
                    'expected': expected,
                    'rate': round((actual / expected) * 100)
                })
        
        # Calculate weekend vs weekday
        weekend_count = day_counts.get('Saturday', 0) + day_counts.get('Sunday', 0)
        weekday_count = actual_workouts - weekend_count
        weekend_rate = (weekend_count / 8) * 100  # 4 weeks * 2 days
        weekday_rate = (weekday_count / 20) * 100  # 4 weeks * 5 days
        
        # Calculate current streak
        streak = cls._calculate_streak(logs)
        
        # Score calculation
        score = completion_rate * 0.7 + (100 - len(problem_days) * 10) * 0.3
        score = max(0, min(100, score))
        
        return {
            'score': round(score),
            'workouts_completed': actual_workouts,
            'workouts_expected': expected_workouts,
            'completion_rate': round(completion_rate),
            'problem_days': problem_days,
            'weekend_rate': round(weekend_rate),
            'weekday_rate': round(weekday_rate),
            'current_streak': streak,
            'status': 'Good' if score >= 80 else 'Needs Improvement' if score >= 60 else 'Critical'
        }
    
    @classmethod
    def _calculate_recovery(cls, logs):
        """Calculate recovery and fatigue score"""
        if not logs.exists():
            return {'score': 50, 'status': 'Unknown'}
        
        # Calculate average perceived effort
        avg_effort = logs.aggregate(Avg('perceived_effort'))['perceived_effort__avg'] or 5
        
        # Analyze feelings
        feeling_counts = defaultdict(int)
        for log in logs:
            feeling_counts[log.how_felt] += 1
        
        total_logs = logs.count()
        tired_rate = (feeling_counts.get('tired', 0) + feeling_counts.get('struggled', 0)) / total_logs * 100
        great_rate = feeling_counts.get('great', 0) / total_logs * 100
        
        # Count rest days in last 14 days
        fourteen_days_ago = datetime.now().date() - timedelta(days=14)
        recent_logs = logs.filter(date__gte=fourteen_days_ago)
        workout_days = set(log.date for log in recent_logs)
        total_days = 14
        rest_days = total_days - len(workout_days)
        
        # Calculate recovery score
        # Lower effort = better (invert scale)
        effort_score = (10 - avg_effort) / 10 * 100
        
        # Less tired = better
        fatigue_score = 100 - tired_rate
        
        # More rest days = better (optimal is 2-3 per week, so 4-6 in 14 days)
        rest_score = min(100, (rest_days / 5) * 100)
        
        # Combined recovery score
        recovery_score = (effort_score * 0.4 + fatigue_score * 0.4 + rest_score * 0.2)
        recovery_score = max(0, min(100, recovery_score))
        
        return {
            'score': round(recovery_score),
            'avg_perceived_effort': round(avg_effort, 1),
            'tired_rate': round(tired_rate),
            'great_rate': round(great_rate),
            'rest_days_14d': rest_days,
            'status': 'Good' if recovery_score >= 70 else 'Warning' if recovery_score >= 50 else 'Critical',
            'overtraining_risk': recovery_score < 50
        }
    
    @classmethod
    def _calculate_goal_progress(cls, athlete):
        """Calculate goal progress score"""
        from performance.models import Goal
        
        active_goals = Goal.objects.filter(athlete=athlete, status='active')
        
        if not active_goals.exists():
            return {
                'score': 50,
                'status': 'No Active Goals',
                'has_goals': False
            }
        
        # Focus on primary goal (most recent)
        goal = active_goals.first()
        
        progress_pct = goal.progress_percentage()
        days_total = (goal.deadline - goal.created_at.date()).days
        days_elapsed = (datetime.now().date() - goal.created_at.date()).days
        days_remaining = (goal.deadline - datetime.now().date()).days
        
        # Calculate expected progress
        expected_progress = (days_elapsed / days_total) * 100 if days_total > 0 else 0
        
        # Calculate if on track
        progress_ratio = progress_pct / expected_progress if expected_progress > 0 else 0
        
        # Score based on progress ratio
        if progress_ratio >= 1.0:
            score = 90 + min(10, (progress_ratio - 1.0) * 50)  # Ahead of schedule
        elif progress_ratio >= 0.8:
            score = 70 + (progress_ratio - 0.8) * 100  # On track
        elif progress_ratio >= 0.6:
            score = 50 + (progress_ratio - 0.6) * 100  # Behind but recoverable
        else:
            score = progress_ratio * 83  # Significantly behind
        
        score = max(0, min(100, score))
        
        # Calculate required improvement rate
        remaining_value = goal.target_value - goal.current_value
        required_rate = remaining_value / days_remaining if days_remaining > 0 else 0
        
        return {
            'score': round(score),
            'goal_name': goal.name,
            'current_value': goal.current_value,
            'target_value': goal.target_value,
            'unit': goal.target_unit,
            'progress_pct': round(progress_pct),
            'days_remaining': days_remaining,
            'expected_progress': round(expected_progress),
            'on_track': progress_ratio >= 0.9,
            'required_rate': round(required_rate, 2),
            'status': 'On Track' if score >= 80 else 'At Risk' if score >= 60 else 'Behind'
        }
    
    @classmethod
    def _calculate_streak(cls, logs):
        """Calculate current workout streak"""
        if not logs.exists():
            return 0
        
        streak = 0
        current_date = datetime.now().date()
        
        # Check if there's a workout today or yesterday
        recent_log = logs.first()
        if (current_date - recent_log.date).days > 1:
            return 0  # Streak broken
        
        # Count consecutive days with workouts
        dates = sorted([log.date for log in logs], reverse=True)
        for i, date in enumerate(dates):
            if i == 0:
                streak = 1
                continue
            
            if (dates[i-1] - date).days == 1:
                streak += 1
            else:
                break
        
        return streak
    
    @classmethod
    def _analyze_root_cause(cls, consistency, recovery, goal):
        """Identify root cause of issues"""
        issues = []
        
        # Check for overtraining
        if recovery['score'] < 60 and recovery.get('rest_days_14d', 0) < 2:
            issues.append({
                'type': 'overtraining',
                'severity': 'critical',
                'description': 'No rest days causing cumulative fatigue'
            })
        
        # Check for fatigue-driven inconsistency
        if consistency['score'] < 80 and recovery['tired_rate'] > 40:
            issues.append({
                'type': 'fatigue_inconsistency',
                'severity': 'high',
                'description': 'Fatigue causing missed workouts'
            })
        
        # Check for slow progress due to poor recovery
        if goal['score'] < 70 and recovery['score'] < 60:
            issues.append({
                'type': 'recovery_limiting_progress',
                'severity': 'high',
                'description': 'Poor recovery limiting workout quality'
            })
        
        # Identify primary root cause
        if recovery['score'] < 60:
            primary_cause = 'poor_recovery'
            chain = [
                'No rest days → High fatigue',
                'High fatigue → Missed workouts',
                'Missed workouts → Slow progress'
            ]
        elif consistency['score'] < 70:
            primary_cause = 'inconsistency'
            chain = [
                'Inconsistent training → Insufficient stimulus',
                'Insufficient stimulus → Slow adaptation',
                'Slow adaptation → Goal at risk'
            ]
        else:
            primary_cause = 'training_quality'
            chain = [
                'Consistent training but slow progress',
                'May need intensity adjustment',
                'Or goal may be too ambitious'
            ]
        
        return {
            'primary_cause': primary_cause,
            'cause_chain': chain,
            'issues': issues,
            'fixable': True
        }
    
    @classmethod
    def _generate_solution_plan(cls, consistency, recovery, goal):
        """Generate phased solution plan"""
        phases = []
        
        # Phase 1: Recovery Reset (if needed)
        if recovery['score'] < 60:
            phases.append({
                'phase': 1,
                'name': 'Recovery Reset',
                'duration': '1-2 weeks',
                'actions': [
                    f"Take {3 - recovery.get('rest_days_14d', 0) // 2} full rest days THIS WEEK",
                    'Reduce all workout intensity to easy pace',
                    'Cut workout duration by 30%',
                    'Sleep 8+ hours every night'
                ],
                'expected_outcome': {
                    'recovery_score': f"{recovery['score']} → 70",
                    'feeling_great': f"{recovery['great_rate']}% → 50%",
                    'energy': 'Improved'
                }
            })
        
        # Phase 2: Build Consistency
        problem_days = consistency.get('problem_days', [])
        if problem_days:
            rest_day = problem_days[0]['day'] if problem_days else 'Tuesday'
            phases.append({
                'phase': 2 if phases else 1,
                'name': 'Smart Consistency',
                'duration': '2-3 weeks',
                'actions': [
                    f'Make {rest_day} a permanent REST DAY',
                    'Add one more rest day mid-week',
                    'Train 4-5 days per week maximum',
                    'Focus on completing scheduled workouts'
                ],
                'expected_outcome': {
                    'consistency': f"{consistency['score']}% → 95%",
                    'missed_days': 'Eliminated',
                    'routine': 'Sustainable'
                }
            })
        
        # Phase 3: Progressive Training
        if goal.get('has_goals', True) and goal['score'] < 80:
            phases.append({
                'phase': len(phases) + 1,
                'name': 'Progressive Training',
                'duration': '4-6 weeks',
                'actions': [
                    'Add speed intervals once per week',
                    'Add tempo run once per week',
                    'Keep other days at easy pace',
                    'Maintain 2 rest days per week'
                ],
                'expected_outcome': {
                    'goal_progress': f"{goal['score']}% → 85%",
                    'improvement_rate': 'Accelerated',
                    'performance': 'Significant gains'
                }
            })
        
        return {
            'phases': phases,
            'total_duration': f"{len(phases) * 2}-{len(phases) * 3} weeks"
        }
    
    @classmethod
    def _generate_coach_feedback(cls, athlete, consistency, recovery, goal, root_cause, solution):
        """Generate ready-to-send coach feedback"""
        athlete_name = athlete.first_name or athlete.username
        
        # Determine tone based on scores
        if recovery['score'] < 50:
            opening = f"I've reviewed your training and I'm concerned about your recovery."
        elif consistency['score'] < 70:
            opening = f"I've been tracking your workouts and see some consistency challenges."
        else:
            opening = f"Your training is looking good overall, but I see room for improvement."
        
        # Build problem section
        problems = []
        if recovery.get('rest_days_14d', 0) == 0:
            problems.append("You haven't taken any rest days in 2 weeks")
        if recovery['tired_rate'] > 40:
            problems.append(f"You're feeling tired after {recovery['tired_rate']:.0f}% of workouts")
        if consistency.get('problem_days'):
            day = consistency['problem_days'][0]['day']
            problems.append(f"You're consistently missing {day}s")
        
        # Build good news section
        good_news = []
        if consistency['weekend_rate'] > 80:
            good_news.append(f"Great weekend consistency ({consistency['weekend_rate']:.0f}%)")
        if consistency['current_streak'] > 3:
            good_news.append(f"You had a {consistency['current_streak']}-day streak")
        if not good_news:
            good_news.append("You're committed and working hard")
        
        # Goal reality check
        if goal.get('has_goals', False):
            if goal['on_track']:
                goal_section = f"You're on track for your goal of {goal['target_value']}{goal['unit']}!"
            else:
                goal_section = f"Your goal of {goal['target_value']}{goal['unit']} needs adjustment. A more realistic target would be {goal['current_value'] + (goal['target_value'] - goal['current_value']) * 0.7:.1f}{goal['unit']}."
        else:
            goal_section = "Let's set a specific goal to work toward!"
        
        feedback = f"""Hi {athlete_name},

{opening}

THE SITUATION:
{chr(10).join(f'• {p}' for p in problems)}

THE GOOD NEWS:
{chr(10).join(f'• {g}' for g in good_news)}

HERE'S THE PLAN:
"""
        
        for phase in solution['phases']:
            feedback += f"\n{phase['name']} ({phase['duration']}):\n"
            for action in phase['actions']:
                feedback += f"  - {action}\n"
        
        feedback += f"\nABOUT YOUR GOAL:\n{goal_section}\n\nWhat do you think? Let's discuss!\n\nYour Coach"
        
        return feedback
    
    @classmethod
    def _calculate_predictions(cls, current_score, consistency, recovery, goal):
        """Predict future scores if plan is followed"""
        predictions = {
            'current': round(current_score),
            'week_2': min(100, round(current_score + 10)),  # Recovery improvement
            'week_4': min(100, round(current_score + 20)),  # Consistency improvement
            'week_8': min(100, round(current_score + 26)),  # Quality improvement
        }
        
        component_predictions = {
            'consistency': {
                'current': consistency['score'],
                'projected': min(100, consistency['score'] + 20)
            },
            'recovery': {
                'current': recovery['score'],
                'projected': min(100, recovery['score'] + 40)
            },
            'goal_progress': {
                'current': goal['score'],
                'projected': min(100, goal['score'] + 20)
            }
        }
        
        return {
            'overall': predictions,
            'components': component_predictions
        }
    
    @classmethod
    def _get_status(cls, score):
        """Get status label from score"""
        if score >= 85:
            return 'Excellent'
        elif score >= 70:
            return 'Good'
        elif score >= 60:
            return 'Needs Improvement'
        else:
            return 'Critical'
    
    @classmethod
    def _generate_no_data_response(cls):
        """Response when no workout data available"""
        return {
            'overall_score': 0,
            'status': 'No Data',
            'message': 'Not enough workout data to calculate TES. Need at least 5 workouts in the last 30 days.',
            'consistency': {'score': 0, 'status': 'No Data'},
            'recovery': {'score': 0, 'status': 'No Data'},
            'goal_progress': {'score': 0, 'status': 'No Data'}
        }
