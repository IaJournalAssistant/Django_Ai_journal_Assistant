from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class MoodEntry(models.Model):
    """Model for storing daily mood entries"""
    
    MOOD_CHOICES = [
        (1, 'Very Low'),
        (2, 'Low'), 
        (3, 'Neutral'),
        (4, 'Good'),
        (5, 'Excellent')
    ]
    
    MOOD_LABELS = [
        ('happy', 'Happy'),
        ('sad', 'Sad'),
        ('anxious', 'Anxious'),
        ('calm', 'Calm'),
        ('energetic', 'Energetic'),
        ('tired', 'Tired'),
        ('focused', 'Focused'),
        ('stressed', 'Stressed'),
        ('content', 'Content'),
        ('frustrated', 'Frustrated'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mood_entries')
    mood_level = models.IntegerField(
        choices=MOOD_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Mood level on a scale of 1-5"
    )
    mood_label = models.CharField(
        max_length=20,
        choices=MOOD_LABELS,
        help_text="Descriptive label for the mood"
    )
    notes = models.TextField(blank=True, help_text="Optional notes about the mood")
    date = models.DateField(default=timezone.now, help_text="Date of the mood entry")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date', '-created_at']
        verbose_name = 'Mood Entry'
        verbose_name_plural = 'Mood Entries'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_mood_label_display()} ({self.mood_level}) on {self.date}"


class Habit(models.Model):
    """Model for storing user habits to track"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habits')
    name = models.CharField(max_length=100, help_text="Name of the habit")
    description = models.TextField(blank=True, help_text="Optional description of the habit")
    is_active = models.BooleanField(default=True, help_text="Whether this habit is currently being tracked")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Habit'
        verbose_name_plural = 'Habits'
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def get_current_streak(self):
        """Calculate the current streak of consecutive completions"""
        from datetime import date, timedelta
        
        today = date.today()
        streak = 0
        current_date = today
        
        while True:
            try:
                log = self.habit_logs.get(date=current_date)
                if log.completed:
                    streak += 1
                    current_date -= timedelta(days=1)
                else:
                    break
            except HabitLog.DoesNotExist:
                break
        
        return streak
    
    def get_completion_rate(self, days=30):
        """Calculate completion rate over the last N days"""
        from datetime import date, timedelta
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        total_days = days
        completed_days = self.habit_logs.filter(
            date__range=[start_date, end_date],
            completed=True
        ).count()
        
        return (completed_days / total_days) * 100 if total_days > 0 else 0


class HabitLog(models.Model):
    """Model for logging daily habit completion"""
    
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='habit_logs')
    date = models.DateField(default=timezone.now, help_text="Date of the habit log")
    completed = models.BooleanField(default=False, help_text="Whether the habit was completed on this date")
    notes = models.TextField(blank=True, help_text="Optional notes about the habit completion")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['habit', 'date']
        ordering = ['-date', '-created_at']
        verbose_name = 'Habit Log'
        verbose_name_plural = 'Habit Logs'
    
    def __str__(self):
        status = "✓" if self.completed else "✗"
        return f"{self.habit.name} - {status} on {self.date}"


class AIInsight(models.Model):
    """Model for storing AI-generated insights and analysis results"""
    
    INSIGHT_TYPES = [
        ('weekly', 'Weekly Analysis'),
        ('monthly', 'Monthly Analysis'),
        ('correlation', 'Mood-Habit Correlation'),
        ('pattern', 'Pattern Analysis'),
        ('recommendation', 'Recommendation'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mood_tracker_ai_insights')
    insight_type = models.CharField(
        max_length=20,
        choices=INSIGHT_TYPES,
        help_text="Type of insight generated"
    )
    content = models.TextField(help_text="The AI-generated insight content")
    generated_at = models.DateTimeField(auto_now_add=True)
    data_period_start = models.DateField(help_text="Start date of the data period analyzed")
    data_period_end = models.DateField(help_text="End date of the data period analyzed")
    is_archived = models.BooleanField(default=False, help_text="Whether this insight has been archived")
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = 'AI Insight'
        verbose_name_plural = 'AI Insights'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_insight_type_display()} ({self.data_period_start} to {self.data_period_end})"
    
    @property
    def data_period_days(self):
        """Calculate the number of days in the analyzed period"""
        return (self.data_period_end - self.data_period_start).days + 1
