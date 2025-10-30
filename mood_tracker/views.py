from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from datetime import date, timedelta
import logging

from .models import MoodEntry, Habit, HabitLog, AIInsight
from .forms import MoodEntryForm, HabitForm, HabitToggleForm
from .utils import (
    get_mood_trend_data, get_mood_statistics, get_mood_calendar_data,
    get_habit_analytics_data, get_habit_completion_heatmap, get_habit_performance_summary
)

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    """Main dashboard view showing mood and habit summary"""
    today = date.today()
    
    try:
        # Get today's mood entry
        today_mood = MoodEntry.objects.filter(user=request.user, date=today).first()
        
        # Get recent mood entries for trend (last 7 days)
        week_ago = today - timedelta(days=6)
        recent_moods = MoodEntry.objects.filter(
            user=request.user,
            date__range=[week_ago, today]
        ).order_by('date')
        
        # Get active habits
        active_habits = Habit.objects.filter(user=request.user, is_active=True)
        
        # Get today's habit logs
        today_habit_logs = {}
        for habit in active_habits:
            try:
                log = HabitLog.objects.filter(habit=habit, date=today).first()
                today_habit_logs[habit.id] = log
            except Exception as e:
                logger.warning(f"Error fetching habit log for {habit.name}: {e}")
                today_habit_logs[habit.id] = None
        
        # Calculate habit stats with error handling
        habit_stats = []
        for habit in active_habits:
            try:
                current_streak = habit.get_current_streak()
                completion_rate_7d = habit.get_completion_rate(7)
                completion_rate_30d = habit.get_completion_rate(30)
                
                habit_stats.append({
                    'habit': habit,
                    'current_streak': current_streak,
                    'completion_rate_7d': completion_rate_7d,
                    'completion_rate_30d': completion_rate_30d,
                    'today_log': today_habit_logs.get(habit.id)
                })
            except Exception as e:
                logger.warning(f"Error calculating stats for habit {habit.name}: {e}")
                # Add habit with default values
                habit_stats.append({
                    'habit': habit,
                    'current_streak': 0,
                    'completion_rate_7d': 0,
                    'completion_rate_30d': 0,
                    'today_log': today_habit_logs.get(habit.id)
                })
        
        # Get mood streak (consecutive days of logging) with error handling
        mood_streak = 0
        try:
            current_date = today
            while True:
                if MoodEntry.objects.filter(user=request.user, date=current_date).exists():
                    mood_streak += 1
                    current_date -= timedelta(days=1)
                else:
                    break
        except Exception as e:
            logger.warning(f"Error calculating mood streak: {e}")
            mood_streak = 0
        
        # Get latest AI insights with error handling
        latest_insights = []
        try:
            latest_insights = AIInsight.objects.filter(
                user=request.user,
                is_archived=False
            )[:2]  # Show only 2 on dashboard
        except Exception as e:
            logger.warning(f"Error fetching AI insights: {e}")
            # Continue without insights
        
        context = {
            'today_mood': today_mood,
            'recent_moods': recent_moods,
            'habit_stats': habit_stats,
            'mood_streak': mood_streak,
            'latest_insights': latest_insights,
            'today': today,
            'dashboard_error': False,
        }
        
    except Exception as e:
        logger.error(f"Critical error in dashboard for user {request.user.username}: {e}")
        # Provide minimal fallback context
        context = {
            'today_mood': None,
            'recent_moods': [],
            'habit_stats': [],
            'mood_streak': 0,
            'latest_insights': [],
            'today': today,
            'dashboard_error': True,
            'error_message': 'Unable to load dashboard data. Please try refreshing the page.',
        }
    
    return render(request, 'mood_tracker/dashboard.html', context)


@login_required
def mood_log(request):
    """View for logging daily mood"""
    today = date.today()
    
    # Check if user already has a mood entry for today
    existing_mood = MoodEntry.objects.filter(user=request.user, date=today).first()
    
    if request.method == 'POST':
        form = MoodEntryForm(request.POST, user=request.user, instance=existing_mood)
        if form.is_valid():
            mood_entry = form.save()
            if existing_mood:
                messages.success(request, 'Your mood entry has been updated successfully!')
            else:
                messages.success(request, 'Your mood has been logged successfully!')
            return redirect('mood_tracker:dashboard')
    else:
        form = MoodEntryForm(user=request.user, instance=existing_mood)
    
    context = {
        'form': form,
        'existing_mood': existing_mood,
        'today': today,
    }
    
    return render(request, 'mood_tracker/mood_log.html', context)


@login_required
def mood_edit(request, pk):
    """View for editing existing mood entry"""
    mood_entry = get_object_or_404(MoodEntry, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = MoodEntryForm(request.POST, user=request.user, instance=mood_entry)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your mood entry has been updated successfully!')
            return redirect('mood_tracker:dashboard')
    else:
        form = MoodEntryForm(user=request.user, instance=mood_entry)
    
    context = {
        'form': form,
        'mood_entry': mood_entry,
    }
    
    return render(request, 'mood_tracker/mood_log.html', context)


@login_required
def mood_delete(request, pk):
    """View for deleting mood entry"""
    mood_entry = get_object_or_404(MoodEntry, pk=pk, user=request.user)
    
    if request.method == 'POST':
        mood_entry.delete()
        messages.success(request, 'Your mood entry has been deleted successfully!')
        return redirect('mood_tracker:dashboard')
    
    context = {
        'mood_entry': mood_entry,
    }
    
    return render(request, 'mood_tracker/mood_delete.html', context)


@login_required
def mood_history(request):
    """View for displaying mood history"""
    mood_entries = MoodEntry.objects.filter(user=request.user).order_by('-date')
    
    context = {
        'mood_entries': mood_entries,
    }
    
    return render(request, 'mood_tracker/mood_history.html', context)


@login_required
def habit_list(request):
    """View for displaying all user habits"""
    habits = Habit.objects.filter(user=request.user).order_by('-is_active', 'name')
    
    # Calculate stats for each habit
    habit_stats = []
    for habit in habits:
        current_streak = habit.get_current_streak()
        completion_rate_7d = habit.get_completion_rate(7)
        completion_rate_30d = habit.get_completion_rate(30)
        
        # Get recent logs for this habit (last 7 days)
        week_ago = date.today() - timedelta(days=6)
        recent_logs = HabitLog.objects.filter(
            habit=habit,
            date__range=[week_ago, date.today()]
        ).order_by('date')
        
        habit_stats.append({
            'habit': habit,
            'current_streak': current_streak,
            'completion_rate_7d': completion_rate_7d,
            'completion_rate_30d': completion_rate_30d,
            'recent_logs': recent_logs,
        })
    
    context = {
        'habit_stats': habit_stats,
    }
    
    return render(request, 'mood_tracker/habit_list.html', context)


@login_required
def habit_create(request):
    """View for creating new habit"""
    if request.method == 'POST':
        form = HabitForm(request.POST, user=request.user)
        if form.is_valid():
            habit = form.save()
            messages.success(request, f'Habit "{habit.name}" has been created successfully!')
            return redirect('mood_tracker:habit_list')
    else:
        form = HabitForm(user=request.user)
    
    context = {
        'form': form,
        'action': 'Create',
    }
    
    return render(request, 'mood_tracker/habit_form.html', context)


@login_required
def habit_edit(request, pk):
    """View for editing existing habit"""
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = HabitForm(request.POST, user=request.user, instance=habit)
        if form.is_valid():
            habit = form.save()
            messages.success(request, f'Habit "{habit.name}" has been updated successfully!')
            return redirect('mood_tracker:habit_list')
    else:
        form = HabitForm(user=request.user, instance=habit)
    
    context = {
        'form': form,
        'habit': habit,
        'action': 'Edit',
    }
    
    return render(request, 'mood_tracker/habit_form.html', context)


@login_required
def habit_delete(request, pk):
    """View for deleting habit"""
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    
    if request.method == 'POST':
        habit_name = habit.name
        habit.delete()
        messages.success(request, f'Habit "{habit_name}" has been deleted successfully!')
        return redirect('mood_tracker:habit_list')
    
    # Get some stats for the habit being deleted
    total_logs = HabitLog.objects.filter(habit=habit).count()
    completed_logs = HabitLog.objects.filter(habit=habit, completed=True).count()
    
    context = {
        'habit': habit,
        'total_logs': total_logs,
        'completed_logs': completed_logs,
    }
    
    return render(request, 'mood_tracker/habit_delete.html', context)


@login_required
def habit_toggle(request, habit_id):
    """HTMX view for toggling habit completion status"""
    try:
        habit = get_object_or_404(Habit, pk=habit_id, user=request.user)
        today = date.today()
        
        # Get or create today's habit log
        habit_log, created = HabitLog.objects.get_or_create(
            habit=habit,
            date=today,
            defaults={'completed': False}
        )
        
        if request.method == 'POST':
            try:
                # Toggle completion status
                habit_log.completed = not habit_log.completed
                habit_log.save()
                
                # Add success message
                if habit_log.completed:
                    messages.success(request, f'Great! You completed "{habit.name}" today!')
                else:
                    messages.info(request, f'Marked "{habit.name}" as not completed for today.')
            except Exception as e:
                logger.error(f"Error toggling habit {habit.name} for user {request.user.username}: {e}")
                messages.error(request, f'Unable to update "{habit.name}". Please try again.')
        
        # Calculate updated stats with error handling
        try:
            current_streak = habit.get_current_streak()
            completion_rate_7d = habit.get_completion_rate(7)
            completion_rate_30d = habit.get_completion_rate(30)
        except Exception as e:
            logger.warning(f"Error calculating habit stats for {habit.name}: {e}")
            current_streak = 0
            completion_rate_7d = 0
            completion_rate_30d = 0
        
        context = {
            'habit': habit,
            'habit_log': habit_log,
            'current_streak': current_streak,
            'completion_rate_7d': completion_rate_7d,
            'completion_rate_30d': completion_rate_30d,
            'toggle_error': False,
        }
        
    except Exception as e:
        logger.error(f"Critical error in habit toggle for habit {habit_id}: {e}")
        # Provide error context for template
        context = {
            'habit': None,
            'habit_log': None,
            'current_streak': 0,
            'completion_rate_7d': 0,
            'completion_rate_30d': 0,
            'toggle_error': True,
            'error_message': 'Unable to update habit. Please refresh and try again.',
        }
        messages.error(request, 'Unable to update habit. Please try again.')
    
    # Return JSON response for HTMX
    if request.headers.get('HX-Request'):
        return render(request, 'mood_tracker/partials/habit_toggle.html', context)
    
    # Fallback for non-HTMX requests
    return redirect('mood_tracker:dashboard')


@login_required
def insights(request):
    """View for displaying AI insights"""
    insights = AIInsight.objects.filter(
        user=request.user,
        is_archived=False
    ).order_by('-generated_at')
    
    # Check AI availability status
    ai_available = False
    django_available = False
    try:
        from .ai_engine import AIAnalysisEngine
        ai_engine = AIAnalysisEngine()
        ai_available = ai_engine.ollama_client.available
        django_available = ai_engine.django_available
    except Exception as e:
        logger.warning(f"Could not check AI availability: {e}")
    
    context = {
        'insights': insights,
        'ai_available': ai_available,
        'django_available': django_available,
    }
    
    return render(request, 'mood_tracker/insights.html', context)


@login_required
def generate_insights(request):
    """View for generating new AI insights"""
    if request.method == 'POST':
        try:
            from .ai_engine import AIAnalysisEngine
            
            # Initialize AI engine with comprehensive error handling
            try:
                ai_engine = AIAnalysisEngine()
            except Exception as e:
                logger.error(f"Failed to initialize AI engine: {e}")
                messages.error(request, 'AI analysis system is currently unavailable. Please try again later.')
                return redirect('mood_tracker:insights')
            
            # Check if Django is available for database operations
            if not ai_engine.django_available:
                messages.error(request, 'Database connection unavailable. Please try again later.')
                return redirect('mood_tracker:insights')
            
            # Check if user has enough data for meaningful insights
            try:
                from datetime import date, timedelta
                week_ago = date.today() - timedelta(days=6)
                mood_count = MoodEntry.objects.filter(user=request.user, date__gte=week_ago).count()
                habit_count = Habit.objects.filter(user=request.user, is_active=True).count()
                
                if mood_count < 3 and habit_count < 1:
                    messages.warning(request, 'You need at least 3 mood entries or 1 active habit to generate meaningful insights. Keep tracking!')
                    return redirect('mood_tracker:insights')
            except Exception as e:
                logger.error(f"Error checking user data for insights: {e}")
                messages.error(request, 'Unable to access your tracking data. Please try again.')
                return redirect('mood_tracker:insights')
            
            # Generate weekly insights with timeout protection
            try:
                insights_data = ai_engine.generate_weekly_insights(request.user)
            except Exception as e:
                logger.error(f"Error during insight generation: {e}")
                messages.error(request, 'Insight generation failed. This may be due to high system load. Please try again in a few minutes.')
                return redirect('mood_tracker:insights')
            
            # Check if insights generation failed
            if insights_data.get('error'):
                error_msg = insights_data.get('message', 'Unknown error occurred during analysis')
                logger.warning(f"Insights generation returned error: {error_msg}")
                messages.error(request, f"Unable to generate insights: {error_msg}")
                return redirect('mood_tracker:insights')
            
            # Save to database with error handling
            try:
                ai_insight = ai_engine.save_insights_to_database(
                    user=request.user,
                    insights=insights_data,
                    insight_type='weekly'
                )
                
                if ai_insight:
                    # Check if AI was available for enhanced insights
                    if ai_engine.ollama_client.available:
                        messages.success(request, 'New AI-powered insights have been generated successfully!')
                    else:
                        messages.success(request, 'New statistical insights have been generated successfully! (AI analysis unavailable)')
                else:
                    messages.warning(request, 'Insights were generated but could not be saved. Please try again.')
            except Exception as e:
                logger.error(f"Error saving insights to database: {e}")
                messages.warning(request, 'Insights were generated but could not be saved. Please try again.')
                
        except ImportError as e:
            logger.error(f"Import error generating insights for user {request.user.username}: {e}")
            messages.error(request, 'AI analysis features are currently unavailable. Please contact support if this persists.')
        except Exception as e:
            logger.error(f"Unexpected error generating insights for user {request.user.username}: {e}")
            messages.error(request, 'An unexpected error occurred. Please try again later or contact support if the problem persists.')
    
    return redirect('mood_tracker:insights')


@login_required
def generate_correlation_insights(request):
    """View for generating correlation-specific insights"""
    if request.method == 'POST':
        try:
            from .ai_engine import AIAnalysisEngine
            
            # Validate and parse days parameter with error handling
            try:
                days = int(request.POST.get('days', 30))
                if days < 7 or days > 365:
                    messages.error(request, 'Please select a valid time period (7-365 days).')
                    return redirect('mood_tracker:insights')
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid days parameter from user {request.user.username}: {e}")
                messages.error(request, 'Invalid time period specified. Please try again.')
                return redirect('mood_tracker:insights')
            
            # Initialize AI engine with comprehensive error handling
            try:
                ai_engine = AIAnalysisEngine()
            except Exception as e:
                logger.error(f"Failed to initialize AI engine for correlation analysis: {e}")
                messages.error(request, 'AI analysis system is currently unavailable. Please try again later.')
                return redirect('mood_tracker:insights')
            
            # Check if Django is available for database operations
            if not ai_engine.django_available:
                messages.error(request, 'Database connection unavailable. Please try again later.')
                return redirect('mood_tracker:insights')
            
            # Check if user has enough data for meaningful correlation analysis
            try:
                from datetime import date, timedelta
                start_date = date.today() - timedelta(days=days-1)
                mood_count = MoodEntry.objects.filter(user=request.user, date__gte=start_date).count()
                habit_count = Habit.objects.filter(user=request.user, is_active=True).count()
                
                if mood_count < 7 or habit_count < 1:
                    messages.warning(request, f'You need at least 7 mood entries and 1 active habit for correlation analysis over {days} days. Keep tracking!')
                    return redirect('mood_tracker:insights')
            except Exception as e:
                logger.error(f"Error checking user data for correlation analysis: {e}")
                messages.error(request, 'Unable to access your tracking data. Please try again.')
                return redirect('mood_tracker:insights')
            
            # Generate correlation insights with timeout protection
            try:
                insights_data = ai_engine.generate_correlation_insights(request.user, days)
            except Exception as e:
                logger.error(f"Error during correlation insight generation: {e}")
                messages.error(request, 'Correlation analysis failed. This may be due to high system load. Please try again in a few minutes.')
                return redirect('mood_tracker:insights')
            
            # Check if insights generation failed
            if insights_data.get('error'):
                error_msg = insights_data.get('message', 'Unknown error occurred during correlation analysis')
                logger.warning(f"Correlation insights generation returned error: {error_msg}")
                messages.error(request, f"Unable to generate correlation insights: {error_msg}")
                return redirect('mood_tracker:insights')
            
            # Save to database with error handling
            try:
                ai_insight = ai_engine.save_insights_to_database(
                    user=request.user,
                    insights=insights_data,
                    insight_type='correlation'
                )
                
                if ai_insight:
                    # Check if AI was available for enhanced insights
                    if ai_engine.ollama_client.available:
                        messages.success(request, f'AI-powered correlation insights for the last {days} days have been generated!')
                    else:
                        messages.success(request, f'Statistical correlation insights for the last {days} days have been generated! (AI analysis unavailable)')
                else:
                    messages.warning(request, 'Correlation insights were generated but could not be saved. Please try again.')
            except Exception as e:
                logger.error(f"Error saving correlation insights to database: {e}")
                messages.warning(request, 'Correlation insights were generated but could not be saved. Please try again.')
                
        except ImportError as e:
            logger.error(f"Import error generating correlation insights for user {request.user.username}: {e}")
            messages.error(request, 'AI analysis features are currently unavailable. Please contact support if this persists.')
        except Exception as e:
            logger.error(f"Unexpected error generating correlation insights for user {request.user.username}: {e}")
            messages.error(request, 'An unexpected error occurred during correlation analysis. Please try again later or contact support if the problem persists.')
    
    return redirect('mood_tracker:insights')


@login_required
def archive_insight(request, insight_id):
    """View for archiving an insight"""
    insight = get_object_or_404(AIInsight, pk=insight_id, user=request.user)
    
    if request.method == 'POST':
        insight.is_archived = True
        insight.save()
        messages.success(request, 'Insight has been archived.')
    
    return redirect('mood_tracker:insights')


@login_required
def insight_detail(request, insight_id):
    """View for displaying detailed insight information"""
    insight = get_object_or_404(AIInsight, pk=insight_id, user=request.user)
    
    context = {
        'insight': insight,
    }
    
    return render(request, 'mood_tracker/insight_detail.html', context)


@login_required
def analytics(request):
    """View for displaying analytics and charts"""
    # Get time period from request (default to 30 days)
    days = int(request.GET.get('days', 30))
    
    # Get mood analytics data
    mood_trend_7d = get_mood_trend_data(request.user, 7)
    mood_trend_30d = get_mood_trend_data(request.user, 30)
    mood_stats_7d = get_mood_statistics(request.user, 7)
    mood_stats_30d = get_mood_statistics(request.user, 30)
    
    # Get mood calendar data for current month
    mood_calendar = get_mood_calendar_data(request.user)
    
    # Get habit analytics data
    habit_analytics = get_habit_analytics_data(request.user, days=days)
    habit_performance = get_habit_performance_summary(request.user, days=days)
    
    # Get basic data for summary
    mood_entries = MoodEntry.objects.filter(user=request.user).order_by('-date')[:30]
    habits = Habit.objects.filter(user=request.user, is_active=True)
    
    context = {
        'mood_entries': mood_entries,
        'habits': habits,
        'mood_trend_7d': mood_trend_7d,
        'mood_trend_30d': mood_trend_30d,
        'mood_stats_7d': mood_stats_7d,
        'mood_stats_30d': mood_stats_30d,
        'mood_calendar': mood_calendar,
        'habit_analytics': habit_analytics,
        'habit_performance': habit_performance,
        'selected_days': days,
    }
    
    return render(request, 'mood_tracker/analytics.html', context)


@login_required
def mood_chart_data(request):
    """API endpoint for mood chart data"""
    days = int(request.GET.get('days', 30))
    chart_data = get_mood_trend_data(request.user, days)
    return JsonResponse(chart_data)


@login_required
def habit_stats(request, habit_id):
    """API endpoint for habit statistics"""
    habit = get_object_or_404(Habit, pk=habit_id, user=request.user)
    days = int(request.GET.get('days', 30))
    
    # Get analytics data for this specific habit
    analytics_data = get_habit_analytics_data(request.user, habit_id, days)
    
    if analytics_data:
        habit_data = analytics_data[0]
        data = {
            'habit_name': habit.name,
            'current_streak': habit_data['current_streak'],
            'completion_rate': habit_data['completion_rate'],
            'total_days': habit_data['total_days'],
            'completed_days': habit_data['completed_days'],
            'longest_streak_in_period': habit_data['longest_streak_in_period'],
            'completion_data': habit_data['completion_data']
        }
    else:
        data = {
            'habit_name': habit.name,
            'current_streak': 0,
            'completion_rate': 0,
            'total_days': days,
            'completed_days': 0,
            'longest_streak_in_period': 0,
            'completion_data': {'labels': [], 'data': [], 'dates': []}
        }
    
    return JsonResponse(data)


@login_required
def mood_calendar_data(request):
    """API endpoint for mood calendar data"""
    year = int(request.GET.get('year', date.today().year))
    month = int(request.GET.get('month', date.today().month))
    
    calendar_data = get_mood_calendar_data(request.user, year, month)
    
    return JsonResponse({
        'year': year,
        'month': month,
        'calendar_data': calendar_data
    })


@login_required
def habit_heatmap_data(request, habit_id):
    """API endpoint for habit completion heatmap data"""
    days = int(request.GET.get('days', 90))
    heatmap_data = get_habit_completion_heatmap(request.user, habit_id, days)
    
    return JsonResponse({
        'heatmap_data': heatmap_data
    })
