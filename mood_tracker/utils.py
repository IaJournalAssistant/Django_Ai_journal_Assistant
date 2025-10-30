"""
Utility functions for mood and habit analytics
"""
from datetime import date, timedelta
from django.db.models import Avg, Count, Q
from .models import MoodEntry, Habit, HabitLog


def get_mood_trend_data(user, days=30):
    """
    Calculate mood trends over the specified number of days
    Returns data suitable for chart visualization
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    # Get mood entries for the period
    mood_entries = MoodEntry.objects.filter(
        user=user,
        date__range=[start_date, end_date]
    ).order_by('date')
    
    # Create a complete date range
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date)
        current_date += timedelta(days=1)
    
    # Build chart data
    chart_data = {
        'labels': [],
        'data': [],
        'colors': [],
        'mood_labels': [],
        'dates': []
    }
    
    # Create a lookup dict for mood entries
    mood_lookup = {entry.date: entry for entry in mood_entries}
    
    for current_date in date_range:
        chart_data['labels'].append(current_date.strftime('%m/%d'))
        chart_data['dates'].append(current_date.strftime('%Y-%m-%d'))
        
        if current_date in mood_lookup:
            mood = mood_lookup[current_date]
            chart_data['data'].append(mood.mood_level)
            chart_data['mood_labels'].append(mood.get_mood_label_display())
            
            # Color based on mood level
            if mood.mood_level <= 2:
                chart_data['colors'].append('#ef4444')  # red
            elif mood.mood_level == 3:
                chart_data['colors'].append('#f59e0b')  # yellow
            else:
                chart_data['colors'].append('#10b981')  # green
        else:
            # No mood entry for this date
            chart_data['data'].append(None)
            chart_data['mood_labels'].append('No entry')
            chart_data['colors'].append('#d1d5db')  # gray
    
    return chart_data


def get_mood_statistics(user, days=30):
    """
    Calculate mood statistics for the specified period
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    mood_entries = MoodEntry.objects.filter(
        user=user,
        date__range=[start_date, end_date]
    )
    
    if not mood_entries.exists():
        return {
            'total_entries': 0,
            'average_mood': 0,
            'mood_distribution': {},
            'streak': 0,
            'best_day': None,
            'worst_day': None
        }
    
    # Basic statistics
    total_entries = mood_entries.count()
    average_mood = mood_entries.aggregate(avg=Avg('mood_level'))['avg'] or 0
    
    # Mood distribution
    mood_distribution = {}
    for level, label in MoodEntry.MOOD_CHOICES:
        count = mood_entries.filter(mood_level=level).count()
        mood_distribution[label] = {
            'count': count,
            'percentage': (count / total_entries * 100) if total_entries > 0 else 0
        }
    
    # Calculate current mood streak
    streak = calculate_mood_streak(user)
    
    # Best and worst days
    best_mood = mood_entries.order_by('-mood_level', '-date').first()
    worst_mood = mood_entries.order_by('mood_level', '-date').first()
    
    return {
        'total_entries': total_entries,
        'average_mood': round(average_mood, 1),
        'mood_distribution': mood_distribution,
        'streak': streak,
        'best_day': best_mood,
        'worst_day': worst_mood
    }


def calculate_mood_streak(user):
    """
    Calculate the current streak of consecutive days with mood entries
    """
    today = date.today()
    streak = 0
    current_date = today
    
    while True:
        if MoodEntry.objects.filter(user=user, date=current_date).exists():
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break
    
    return streak


def get_mood_calendar_data(user, year=None, month=None):
    """
    Get mood data for calendar view
    """
    if year is None:
        year = date.today().year
    if month is None:
        month = date.today().month
    
    # Get first and last day of the month
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    
    mood_entries = MoodEntry.objects.filter(
        user=user,
        date__range=[first_day, last_day]
    )
    
    # Create calendar data structure
    calendar_data = {}
    for mood in mood_entries:
        calendar_data[mood.date.day] = {
            'mood_level': mood.mood_level,
            'mood_label': mood.get_mood_label_display(),
            'notes': mood.notes
        }
    
    return calendar_data


def get_habit_analytics_data(user, habit_id=None, days=30):
    """
    Get habit analytics data for visualization
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    if habit_id:
        habits = Habit.objects.filter(id=habit_id, user=user)
    else:
        habits = Habit.objects.filter(user=user, is_active=True)
    
    analytics_data = []
    
    for habit in habits:
        # Get habit logs for the period
        logs = HabitLog.objects.filter(
            habit=habit,
            date__range=[start_date, end_date]
        ).order_by('date')
        
        # Create date range for this habit
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date)
            current_date += timedelta(days=1)
        
        # Build completion data
        completion_data = {
            'labels': [],
            'data': [],
            'dates': []
        }
        
        log_lookup = {log.date: log for log in logs}
        
        for current_date in date_range:
            completion_data['labels'].append(current_date.strftime('%m/%d'))
            completion_data['dates'].append(current_date.strftime('%Y-%m-%d'))
            
            if current_date in log_lookup:
                completion_data['data'].append(1 if log_lookup[current_date].completed else 0)
            else:
                completion_data['data'].append(0)
        
        # Calculate statistics
        total_days = len(date_range)
        completed_days = sum(completion_data['data'])
        completion_rate = (completed_days / total_days * 100) if total_days > 0 else 0
        current_streak = habit.get_current_streak()
        
        # Calculate longest streak in the period
        longest_streak = 0
        current_period_streak = 0
        for completed in completion_data['data']:
            if completed:
                current_period_streak += 1
                longest_streak = max(longest_streak, current_period_streak)
            else:
                current_period_streak = 0
        
        # Calculate weekly completion rates
        weekly_rates = calculate_weekly_completion_rates(completion_data['data'], days)
        
        # Calculate best and worst days of week
        best_day, worst_day = calculate_best_worst_days(habit, days)
        
        analytics_data.append({
            'habit': habit,
            'completion_data': completion_data,
            'total_days': total_days,
            'completed_days': completed_days,
            'completion_rate': round(completion_rate, 1),
            'current_streak': current_streak,
            'longest_streak_in_period': longest_streak,
            'weekly_rates': weekly_rates,
            'best_day_of_week': best_day,
            'worst_day_of_week': worst_day
        })
    
    return analytics_data


def calculate_weekly_completion_rates(completion_data, total_days):
    """
    Calculate completion rates for each week in the period
    """
    if total_days < 7:
        return []
    
    weekly_rates = []
    weeks = total_days // 7
    
    for week in range(weeks):
        start_idx = week * 7
        end_idx = start_idx + 7
        week_data = completion_data[start_idx:end_idx]
        
        if week_data:
            completed = sum(week_data)
            rate = (completed / len(week_data)) * 100
            weekly_rates.append(round(rate, 1))
    
    return weekly_rates


def calculate_best_worst_days(habit, days=30):
    """
    Calculate which days of the week the user is most/least likely to complete the habit
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    logs = HabitLog.objects.filter(
        habit=habit,
        date__range=[start_date, end_date]
    )
    
    # Count completions by day of week (0=Monday, 6=Sunday)
    day_stats = {i: {'completed': 0, 'total': 0} for i in range(7)}
    
    current_date = start_date
    while current_date <= end_date:
        day_of_week = current_date.weekday()
        day_stats[day_of_week]['total'] += 1
        
        log = logs.filter(date=current_date).first()
        if log and log.completed:
            day_stats[day_of_week]['completed'] += 1
        
        current_date += timedelta(days=1)
    
    # Calculate completion rates for each day
    day_rates = {}
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for day_idx, stats in day_stats.items():
        if stats['total'] > 0:
            rate = (stats['completed'] / stats['total']) * 100
            day_rates[day_names[day_idx]] = round(rate, 1)
        else:
            day_rates[day_names[day_idx]] = 0
    
    # Find best and worst days
    if day_rates:
        best_day = max(day_rates, key=day_rates.get)
        worst_day = min(day_rates, key=day_rates.get)
        return best_day, worst_day
    
    return None, None


def get_habit_performance_summary(user, days=30):
    """
    Get overall habit performance summary
    """
    habits = Habit.objects.filter(user=user, is_active=True)
    
    if not habits.exists():
        return {
            'total_habits': 0,
            'average_completion_rate': 0,
            'best_performing_habit': None,
            'worst_performing_habit': None,
            'total_completions': 0
        }
    
    habit_analytics = get_habit_analytics_data(user, days=days)
    
    total_habits = len(habit_analytics)
    total_completion_rate = sum(h['completion_rate'] for h in habit_analytics)
    average_completion_rate = total_completion_rate / total_habits if total_habits > 0 else 0
    
    best_habit = max(habit_analytics, key=lambda x: x['completion_rate']) if habit_analytics else None
    worst_habit = min(habit_analytics, key=lambda x: x['completion_rate']) if habit_analytics else None
    
    total_completions = sum(h['completed_days'] for h in habit_analytics)
    
    return {
        'total_habits': total_habits,
        'average_completion_rate': round(average_completion_rate, 1),
        'best_performing_habit': best_habit,
        'worst_performing_habit': worst_habit,
        'total_completions': total_completions
    }


def get_habit_completion_heatmap(user, habit_id, days=90):
    """
    Get habit completion data for heatmap visualization
    """
    habit = Habit.objects.get(id=habit_id, user=user)
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    logs = HabitLog.objects.filter(
        habit=habit,
        date__range=[start_date, end_date]
    )
    
    heatmap_data = []
    current_date = start_date
    
    log_lookup = {log.date: log for log in logs}
    
    while current_date <= end_date:
        heatmap_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'value': 1 if current_date in log_lookup and log_lookup[current_date].completed else 0,
            'day': current_date.strftime('%a'),
            'week': current_date.isocalendar()[1]
        })
        current_date += timedelta(days=1)
    
    return heatmap_data