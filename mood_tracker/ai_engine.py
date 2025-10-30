"""
AI Analysis Engine for Mood and Habit Tracking

This module provides AI-powered analysis and insights for mood and habit data.
It includes statistical analysis functions and integrates with local AI models via Ollama.
"""

import json
import logging
import requests
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import pearsonr, spearmanr

logger = logging.getLogger(__name__)


def _safe_django_import():
    """
    Safely import Django components with proper error handling
    
    Returns:
        Tuple of (success, imports_dict, error_message)
    """
    try:
        import django
        from django.conf import settings
        
        # Check if Django is configured
        if not settings.configured:
            return False, {}, "Django settings not configured"
        
        # Import Django components
        from django.contrib.auth.models import User
        from django.db.models import Avg, Count, Q
        from django.utils import timezone
        from django.core.cache import cache
        from django.utils.encoding import force_str
        from .models import MoodEntry, Habit, HabitLog, AIInsight
        
        return True, {
            'User': User,
            'Avg': Avg,
            'Count': Count,
            'Q': Q,
            'timezone': timezone,
            'cache': cache,
            'force_str': force_str,
            'MoodEntry': MoodEntry,
            'Habit': Habit,
            'HabitLog': HabitLog,
            'AIInsight': AIInsight
        }, None
        
    except Exception as e:
        return False, {}, str(e)


class OllamaClient:
    """
    Client for interacting with local Ollama AI models
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:11434", model: str = "gemma3:1b"):
        self.base_url = base_url
        self.model = model
        self.logger = logging.getLogger(__name__ + '.OllamaClient')
        self.available = self._check_availability()
        self.django_available = False
        self.django_imports = {}
        self._check_django_availability()
    
    def _check_availability(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Ollama not available: {e}")
            return False
    
    def _check_django_availability(self) -> None:
        """Check if Django is available and properly configured"""
        try:
            success, imports, error = _safe_django_import()
            if success:
                self.django_available = True
                self.django_imports = imports
                self.logger.info("Django components loaded successfully")
            else:
                self.django_available = False
                self.logger.warning(f"Django not available: {error}")
        except Exception as e:
            self.django_available = False
            self.logger.error(f"Error checking Django availability: {e}")
    
    def generate_insight(self, prompt: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Generate AI insight using Ollama
        
        Args:
            prompt: The prompt for the AI model
            context: Additional context data
            
        Returns:
            Generated insight text or None if failed
        """
        if not self.available:
            self.logger.warning("Ollama not available, skipping AI generation")
            return None
        
        try:
            # Prepare the full prompt with context
            full_prompt = self._build_prompt(prompt, context)
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                self.logger.error(f"Ollama API error: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating insight: {e}")
            return None
    
    def _build_prompt(self, base_prompt: str, context: Dict[str, Any]) -> str:
        """Build a comprehensive prompt with context"""
        context_str = json.dumps(context, indent=2, default=str)
        
        return f"""You are a helpful AI assistant specializing in mood and habit analysis. 
Provide personalized, actionable insights based on the user's data.

Context Data:
{context_str}

Task: {base_prompt}

Please provide a clear, encouraging, and actionable insight in 2-3 sentences. 
Focus on practical recommendations the user can implement."""
    
    def check_model_availability(self) -> Dict[str, Any]:
        """Check which models are available"""
        if not self.available:
            return {"available": False, "models": []}
        
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                return {"available": True, "models": models}
        except Exception as e:
            self.logger.error(f"Error checking models: {e}")
        
        return {"available": False, "models": []}


class AIAnalysisEngine:
    """
    Main AI analysis engine that combines statistical analysis with AI insights
    """
    
    def __init__(self):
        self.statistical_analyzer = StatisticalAnalyzer()
        self.data_aggregator = DataAggregator()
        self.ollama_client = OllamaClient()
        self.logger = logging.getLogger(__name__ + '.AIAnalysisEngine')
        self.django_available = False
        self.django_imports = {}
        self._check_django_availability()
    
    def _check_django_availability(self) -> None:
        """Check if Django is available and properly configured"""
        try:
            success, imports, error = _safe_django_import()
            if success:
                self.django_available = True
                self.django_imports = imports
                self.logger.info("Django components loaded successfully for AIAnalysisEngine")
            else:
                self.django_available = False
                self.logger.warning(f"Django not available for AIAnalysisEngine: {error}")
        except Exception as e:
            self.django_available = False
            self.logger.error(f"Error checking Django availability in AIAnalysisEngine: {e}")
    
    def generate_weekly_insights(self, user) -> Dict[str, Any]:
        """
        Generate comprehensive weekly insights combining statistical analysis and AI
        
        Args:
            user: Django User instance
            
        Returns:
            Dictionary containing insights and analysis
        """
        if not self.django_available:
            return self._generate_error_insights("Django not available - cannot access database")
        
        try:
            cache = self.django_imports['cache']
            timezone = self.django_imports['timezone']
            
            # Check cache first
            cache_key = f"weekly_insights_{user.id}_{date.today().isoformat()}"
            cached_insights = cache.get(cache_key)
            if cached_insights:
                self.logger.info(f"Returning cached weekly insights for user {user.username}")
                return cached_insights
        except Exception as e:
            self.logger.warning(f"Cache check failed: {e}")
            # Continue without cache
        
        try:
            timezone = self.django_imports.get('timezone')
            
            # Get statistical analysis
            mood_analysis = self.statistical_analyzer.analyze_mood_patterns(user, days=7)
            habit_analysis = self.statistical_analyzer.analyze_habit_patterns(user, days=7)
            correlation_analysis = self.statistical_analyzer.analyze_mood_habit_correlations(user, days=7)
            
            # Get summary data for AI context
            summary_stats = self.data_aggregator.calculate_summary_statistics(user, days=7)
            
            insights = {
                'period': 'weekly',
                'generated_at': timezone.now() if timezone else date.today().isoformat(),
                'statistical_analysis': {
                    'mood': mood_analysis,
                    'habits': habit_analysis,
                    'correlations': correlation_analysis
                },
                'ai_insights': {},
                'recommendations': [],
                'data_quality': summary_stats
            }
            
            # Generate AI insights if available
            if self.ollama_client.available:
                ai_insights = self._generate_ai_insights(user, summary_stats, mood_analysis, habit_analysis, correlation_analysis)
                insights['ai_insights'] = ai_insights
            else:
                # Fallback to statistical recommendations
                insights['ai_insights'] = self._generate_statistical_insights(mood_analysis, habit_analysis, correlation_analysis)
            
            # Combine recommendations
            insights['recommendations'] = self._combine_recommendations(insights)
            
            # Cache the results for 6 hours if cache is available
            try:
                cache = self.django_imports.get('cache')
                if cache:
                    cache.set(cache_key, insights, 60 * 60 * 6)
            except Exception as e:
                self.logger.warning(f"Failed to cache insights: {e}")
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating weekly insights: {e}")
            return self._generate_error_insights(str(e))
    
    def generate_correlation_insights(self, user, days: int = 30) -> Dict[str, Any]:
        """
        Generate insights focused on mood-habit correlations
        
        Args:
            user: Django User instance
            days: Number of days to analyze
            
        Returns:
            Dictionary containing correlation insights
        """
        if not self.django_available:
            return self._generate_error_insights("Django not available - cannot access database")
        
        try:
            cache = self.django_imports.get('cache')
            timezone = self.django_imports.get('timezone')
            
            # Check cache first
            cache_key = f"correlation_insights_{user.id}_{days}_{date.today().isoformat()}"
            if cache:
                cached_insights = cache.get(cache_key)
                if cached_insights:
                    self.logger.info(f"Returning cached correlation insights for user {user.username}")
                    return cached_insights
        except Exception as e:
            self.logger.warning(f"Cache check failed: {e}")
            # Continue without cache
        
        try:
            correlation_analysis = self.statistical_analyzer.analyze_mood_habit_correlations(user, days)
            summary_stats = self.data_aggregator.calculate_summary_statistics(user, days)
            
            insights = {
                'period': f'{days}_days',
                'generated_at': timezone.now() if timezone else date.today().isoformat(),
                'correlation_analysis': correlation_analysis,
                'ai_insights': {},
                'recommendations': [],
                'data_quality': summary_stats
            }
            
            # Generate AI insights for correlations
            if self.ollama_client.available and correlation_analysis['correlations']:
                context = {
                    'correlations': correlation_analysis['correlations'],
                    'patterns': correlation_analysis['patterns'],
                    'data_quality': correlation_analysis['data_quality']
                }
                
                prompt = "Analyze the mood-habit correlations and provide actionable insights about which habits most impact mood."
                ai_insight = self.ollama_client.generate_insight(prompt, context)
                
                if ai_insight:
                    insights['ai_insights']['correlation_summary'] = ai_insight
            
            # Add statistical insights as fallback
            insights['ai_insights']['statistical_insights'] = correlation_analysis['insights']
            insights['recommendations'] = correlation_analysis['insights']
            
            # Cache the results for 4 hours if cache is available
            try:
                if cache:
                    cache.set(cache_key, insights, 60 * 60 * 4)
            except Exception as e:
                self.logger.warning(f"Failed to cache correlation insights: {e}")
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating correlation insights: {e}")
            return self._generate_error_insights(str(e))
    
    def generate_habit_recommendations(self, user, habit_name: str, days: int = 30) -> Dict[str, Any]:
        """
        Generate specific recommendations for a habit
        
        Args:
            user: Django User instance
            habit_name: Name of the habit to analyze
            days: Number of days to analyze
            
        Returns:
            Dictionary containing habit-specific insights
        """
        if not self.django_available:
            return self._generate_error_insights("Django not available - cannot access database")
        
        try:
            timezone = self.django_imports.get('timezone')
            habit_analysis = self.statistical_analyzer.analyze_habit_patterns(user, days)
            
            if habit_name not in habit_analysis:
                return {'error': f'Habit "{habit_name}" not found in analysis'}
            
            habit_data = habit_analysis[habit_name]
            
            insights = {
                'habit_name': habit_name,
                'period': f'{days}_days',
                'generated_at': timezone.now() if timezone else date.today().isoformat(),
                'analysis': habit_data,
                'ai_insights': {},
                'recommendations': habit_data['recommendations']
            }
            
            # Generate AI recommendations if available
            if self.ollama_client.available:
                context = {
                    'habit_name': habit_name,
                    'completion_stats': habit_data['completion_stats'],
                    'streaks': habit_data['streaks'],
                    'patterns': habit_data['patterns'],
                    'day_analysis': habit_data['day_of_week_analysis']
                }
                
                prompt = f"Provide specific, actionable recommendations to improve consistency with the '{habit_name}' habit."
                ai_insight = self.ollama_client.generate_insight(prompt, context)
                
                if ai_insight:
                    insights['ai_insights']['personalized_recommendations'] = ai_insight
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating habit recommendations: {e}")
            return self._generate_error_insights(str(e))
    
    def _generate_ai_insights(self, user, summary_stats: Dict, mood_analysis: Dict, habit_analysis: Dict, correlation_analysis: Dict) -> Dict[str, Any]:
        """Generate AI insights using Ollama"""
        ai_insights = {}
        
        # Mood insights
        if mood_analysis['basic_stats']['count'] > 0:
            mood_context = {
                'average_mood': mood_analysis['basic_stats']['mean'],
                'mood_trend': mood_analysis['trends']['trend'],
                'volatility': mood_analysis['volatility']['classification'],
                'patterns': mood_analysis['patterns']
            }
            
            mood_prompt = "Analyze the user's mood patterns and provide encouraging insights with actionable suggestions."
            mood_insight = self.ollama_client.generate_insight(mood_prompt, mood_context)
            if mood_insight:
                ai_insights['mood_summary'] = mood_insight
        
        # Habit insights
        if habit_analysis:
            habit_context = {
                'habits': {name: data['completion_stats'] for name, data in habit_analysis.items()},
                'overall_performance': summary_stats['habits']['completion_rates']
            }
            
            habit_prompt = "Analyze the user's habit completion patterns and suggest improvements."
            habit_insight = self.ollama_client.generate_insight(habit_prompt, habit_context)
            if habit_insight:
                ai_insights['habit_summary'] = habit_insight
        
        # Correlation insights
        if correlation_analysis['correlations']:
            correlation_context = {
                'significant_correlations': correlation_analysis['correlations'],
                'patterns': correlation_analysis['patterns']
            }
            
            correlation_prompt = "Explain how the user's habits relate to their mood and suggest optimization strategies."
            correlation_insight = self.ollama_client.generate_insight(correlation_prompt, correlation_context)
            if correlation_insight:
                ai_insights['correlation_summary'] = correlation_insight
        
        return ai_insights
    
    def _generate_statistical_insights(self, mood_analysis: Dict, habit_analysis: Dict, correlation_analysis: Dict) -> Dict[str, Any]:
        """Generate insights using only statistical analysis (fallback)"""
        insights = {}
        
        # Mood insights
        if mood_analysis['basic_stats']['count'] > 0:
            avg_mood = mood_analysis['basic_stats']['mean']
            trend = mood_analysis['trends']['trend']
            
            if avg_mood >= 4:
                mood_summary = "Your mood has been consistently positive this week. Keep up the great work!"
            elif avg_mood >= 3:
                mood_summary = "Your mood has been fairly stable around neutral. Consider activities that might boost your mood."
            else:
                mood_summary = "Your mood has been below average this week. Focus on self-care and mood-boosting activities."
            
            if trend == 'improving':
                mood_summary += " The positive trend in your mood is encouraging."
            elif trend == 'declining':
                mood_summary += " Your mood trend suggests focusing on what might be causing the decline."
            
            insights['mood_summary'] = mood_summary
        
        # Habit insights
        if habit_analysis:
            completion_rates = [data['completion_stats']['completion_rate'] for data in habit_analysis.values()]
            avg_completion = sum(completion_rates) / len(completion_rates) if completion_rates else 0
            
            if avg_completion >= 80:
                habit_summary = "Excellent habit consistency this week! You're building strong routines."
            elif avg_completion >= 60:
                habit_summary = "Good progress on your habits. Focus on the ones you're struggling with most."
            else:
                habit_summary = "Your habit completion could use improvement. Consider making your habits easier or more rewarding."
            
            insights['habit_summary'] = habit_summary
        
        # Correlation insights
        if correlation_analysis['patterns'].get('mood_boosting_habits'):
            habits = [h['name'] for h in correlation_analysis['patterns']['mood_boosting_habits']]
            insights['correlation_summary'] = f"These habits seem to boost your mood: {', '.join(habits)}. Prioritize them!"
        
        return insights
    
    def _combine_recommendations(self, insights: Dict[str, Any]) -> List[str]:
        """Combine recommendations from different analysis sources"""
        recommendations = []
        
        # Add statistical recommendations
        mood_recs = insights['statistical_analysis']['mood'].get('recommendations', [])
        recommendations.extend(mood_recs)
        
        for habit_data in insights['statistical_analysis']['habits'].values():
            recommendations.extend(habit_data.get('recommendations', []))
        
        # Add correlation insights
        correlation_insights = insights['statistical_analysis']['correlations'].get('insights', [])
        recommendations.extend(correlation_insights)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:5]  # Limit to top 5 recommendations
    
    def _generate_error_insights(self, error_message: str) -> Dict[str, Any]:
        """Generate error response for insights"""
        try:
            timezone = self.django_imports.get('timezone')
            generated_at = timezone.now() if timezone else date.today().isoformat()
        except:
            generated_at = date.today().isoformat()
        
        return {
            'error': True,
            'message': 'Unable to generate insights at this time',
            'details': error_message,
            'generated_at': generated_at,
            'recommendations': ['Please try again later or contact support if the issue persists.']
        }
    
    def save_insights_to_database(self, user, insights: Dict[str, Any], insight_type: str = 'weekly'):
        """
        Save generated insights to the database
        
        Args:
            user: Django User instance
            insights: Generated insights dictionary
            insight_type: Type of insight (weekly, monthly, correlation, etc.)
            
        Returns:
            Created AIInsight instance or None if failed
        """
        if not self.django_available:
            self.logger.warning("Django not available - cannot save insights to database")
            return None
        
        try:
            AIInsight = self.django_imports['AIInsight']
            # Determine data period
            if insight_type == 'weekly':
                end_date = date.today()
                start_date = end_date - timedelta(days=6)
            elif insight_type == 'monthly':
                end_date = date.today()
                start_date = end_date - timedelta(days=29)
            else:
                # Default to weekly
                end_date = date.today()
                start_date = end_date - timedelta(days=6)
            
            # Create content from insights
            content_parts = []
            
            if 'ai_insights' in insights:
                for key, value in insights['ai_insights'].items():
                    if isinstance(value, str):
                        content_parts.append(f"{key.replace('_', ' ').title()}: {value}")
            
            if 'recommendations' in insights:
                content_parts.append("Recommendations:")
                for i, rec in enumerate(insights['recommendations'][:3], 1):
                    content_parts.append(f"{i}. {rec}")
            
            content = "\n\n".join(content_parts) if content_parts else "Analysis completed successfully."
            
            # Create AIInsight record
            ai_insight = AIInsight.objects.create(
                user=user,
                insight_type=insight_type,
                content=content,
                data_period_start=start_date,
                data_period_end=end_date
            )
            
            self.logger.info(f"Saved {insight_type} insights for user {user.username}")
            return ai_insight
            
        except Exception as e:
            self.logger.error(f"Error saving insights to database: {e}")
            return None


class StatisticalAnalyzer:
    """
    Statistical analysis engine for mood and habit data
    Provides fallback analysis when AI models are unavailable
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + '.StatisticalAnalyzer')
        self.django_available = False
        self.django_imports = {}
        self._check_django_availability()
    
    def _check_django_availability(self) -> None:
        """Check if Django is available and properly configured"""
        try:
            success, imports, error = _safe_django_import()
            if success:
                self.django_available = True
                self.django_imports = imports
                self.logger.info("Django components loaded successfully for StatisticalAnalyzer")
            else:
                self.django_available = False
                self.logger.warning(f"Django not available for StatisticalAnalyzer: {error}")
        except Exception as e:
            self.django_available = False
            self.logger.error(f"Error checking Django availability in StatisticalAnalyzer: {e}")
    
    def analyze_mood_patterns(self, user, days: int = 30) -> Dict[str, Any]:
        """
        Analyze mood patterns using statistical methods
        
        Args:
            user: Django User instance
            days: Number of days to analyze
            
        Returns:
            Dictionary containing mood pattern analysis
        """
        if not self.django_available:
            return self._empty_mood_analysis()
        
        try:
            MoodEntry = self.django_imports['MoodEntry']
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days-1)
            
            mood_entries = MoodEntry.objects.filter(
                user=user,
                date__range=[start_date, end_date]
            ).order_by('date')
        except Exception as e:
            self.logger.error(f"Error accessing mood data: {e}")
            return self._empty_mood_analysis()
        
        if not mood_entries.exists():
            return self._empty_mood_analysis()
        
        # Convert to pandas DataFrame for analysis
        mood_data = []
        for entry in mood_entries:
            mood_data.append({
                'date': entry.date,
                'mood_level': entry.mood_level,
                'mood_label': entry.mood_label,
                'day_of_week': entry.date.weekday(),
                'week_of_year': entry.date.isocalendar()[1]
            })
        
        df = pd.DataFrame(mood_data)
        
        analysis = {
            'basic_stats': self._calculate_mood_basic_stats(df),
            'trends': self._analyze_mood_trends(df),
            'patterns': self._detect_mood_patterns(df),
            'volatility': self._calculate_mood_volatility(df),
            'day_of_week_analysis': self._analyze_day_of_week_patterns(df),
            'recommendations': self._generate_mood_recommendations(df)
        }
        
        return analysis
    
    def analyze_habit_patterns(self, user, days: int = 30) -> Dict[str, Any]:
        """
        Analyze habit completion patterns using statistical methods
        
        Args:
            user: Django User instance
            days: Number of days to analyze
            
        Returns:
            Dictionary containing habit pattern analysis
        """
        if not self.django_available:
            return self._empty_habit_analysis()
        
        try:
            Habit = self.django_imports['Habit']
            HabitLog = self.django_imports['HabitLog']
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days-1)
            
            habits = Habit.objects.filter(user=user, is_active=True)
        except Exception as e:
            self.logger.error(f"Error accessing habit data: {e}")
            return self._empty_habit_analysis()
        
        if not habits.exists():
            return self._empty_habit_analysis()
        
        habit_analysis = {}
        
        for habit in habits:
            try:
                logs = HabitLog.objects.filter(
                    habit=habit,
                    date__range=[start_date, end_date]
                ).order_by('date')
            except Exception as e:
                self.logger.error(f"Error accessing habit logs for {habit.name}: {e}")
                continue
            
            # Create complete date range with completion data
            habit_data = []
            current_date = start_date
            log_lookup = {log.date: log for log in logs}
            
            while current_date <= end_date:
                completed = current_date in log_lookup and log_lookup[current_date].completed
                habit_data.append({
                    'date': current_date,
                    'completed': 1 if completed else 0,
                    'day_of_week': current_date.weekday(),
                    'week_of_year': current_date.isocalendar()[1]
                })
                current_date += timedelta(days=1)
            
            df = pd.DataFrame(habit_data)
            
            habit_analysis[habit.name] = {
                'completion_stats': self._calculate_habit_completion_stats(df),
                'streaks': self._analyze_habit_streaks(df),
                'patterns': self._detect_habit_patterns(df),
                'day_of_week_analysis': self._analyze_habit_day_patterns(df),
                'recommendations': self._generate_habit_recommendations(df, habit.name)
            }
        
        return habit_analysis
    
    def analyze_mood_habit_correlations(self, user, days: int = 30) -> Dict[str, Any]:
        """
        Analyze correlations between mood and habit completion
        
        Args:
            user: Django User instance
            days: Number of days to analyze
            
        Returns:
            Dictionary containing correlation analysis
        """
        if not self.django_available:
            return self._empty_correlation_analysis()
        
        try:
            MoodEntry = self.django_imports['MoodEntry']
            Habit = self.django_imports['Habit']
            HabitLog = self.django_imports['HabitLog']
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days-1)
            
            # Get mood data
            mood_entries = MoodEntry.objects.filter(
                user=user,
                date__range=[start_date, end_date]
            )
            
            # Get habit data
            habits = Habit.objects.filter(user=user, is_active=True)
        except Exception as e:
            self.logger.error(f"Error accessing correlation data: {e}")
            return self._empty_correlation_analysis()
        
        if not mood_entries.exists() or not habits.exists():
            return self._empty_correlation_analysis()
        
        # Create combined dataset
        combined_data = []
        current_date = start_date
        
        mood_lookup = {entry.date: entry for entry in mood_entries}
        
        while current_date <= end_date:
            if current_date in mood_lookup:
                mood_entry = mood_lookup[current_date]
                row = {
                    'date': current_date,
                    'mood_level': mood_entry.mood_level,
                    'mood_label': mood_entry.mood_label
                }
                
                # Add habit completion data for this date
                for habit in habits:
                    try:
                        log = HabitLog.objects.filter(habit=habit, date=current_date).first()
                        row[f'habit_{habit.id}'] = 1 if log and log.completed else 0
                        row[f'habit_{habit.id}_name'] = habit.name
                    except Exception as e:
                        self.logger.error(f"Error accessing habit log for {habit.name} on {current_date}: {e}")
                        row[f'habit_{habit.id}'] = 0
                        row[f'habit_{habit.id}_name'] = habit.name
                
                combined_data.append(row)
            
            current_date += timedelta(days=1)
        
        if not combined_data:
            return self._empty_correlation_analysis()
        
        df = pd.DataFrame(combined_data)
        
        correlations = self._calculate_mood_habit_correlations(df, habits)
        patterns = self._detect_correlation_patterns(df, habits)
        insights = self._generate_correlation_insights(correlations, patterns)
        
        return {
            'correlations': correlations,
            'patterns': patterns,
            'insights': insights,
            'data_quality': self._assess_correlation_data_quality(df)
        }
    
    def _calculate_mood_basic_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic mood statistics"""
        return {
            'mean': float(df['mood_level'].mean()),
            'median': float(df['mood_level'].median()),
            'std': float(df['mood_level'].std()),
            'min': int(df['mood_level'].min()),
            'max': int(df['mood_level'].max()),
            'count': len(df),
            'mood_distribution': df['mood_level'].value_counts().to_dict()
        }
    
    def _analyze_mood_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze mood trends over time"""
        if len(df) < 3:
            return {'trend': 'insufficient_data', 'slope': 0, 'r_squared': 0}
        
        # Calculate linear trend
        x = np.arange(len(df))
        y = df['mood_level'].values
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        trend_direction = 'improving' if slope > 0.05 else 'declining' if slope < -0.05 else 'stable'
        
        return {
            'trend': trend_direction,
            'slope': float(slope),
            'r_squared': float(r_value ** 2),
            'p_value': float(p_value),
            'significance': 'significant' if p_value < 0.05 else 'not_significant'
        }
    
    def _detect_mood_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect patterns in mood data"""
        patterns = {}
        
        # Weekly patterns
        weekly_avg = df.groupby('day_of_week')['mood_level'].mean()
        patterns['weekly'] = {
            'best_day': int(weekly_avg.idxmax()),
            'worst_day': int(weekly_avg.idxmin()),
            'variation': float(weekly_avg.std())
        }
        
        # Volatility patterns
        df['mood_change'] = df['mood_level'].diff()
        patterns['volatility'] = {
            'high_volatility_days': len(df[abs(df['mood_change']) > 2]),
            'avg_daily_change': float(abs(df['mood_change']).mean())
        }
        
        return patterns
    
    def _calculate_mood_volatility(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate mood volatility metrics"""
        if len(df) < 2:
            return {'volatility': 0, 'stability_score': 100}
        
        volatility = float(df['mood_level'].std())
        stability_score = max(0, 100 - (volatility * 20))  # Scale volatility to 0-100
        
        return {
            'volatility': volatility,
            'stability_score': stability_score,
            'classification': self._classify_volatility(volatility)
        }
    
    def _classify_volatility(self, volatility: float) -> str:
        """Classify mood volatility level"""
        if volatility < 0.5:
            return 'very_stable'
        elif volatility < 1.0:
            return 'stable'
        elif volatility < 1.5:
            return 'moderate'
        elif volatility < 2.0:
            return 'volatile'
        else:
            return 'very_volatile'
    
    def _analyze_day_of_week_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze mood patterns by day of week"""
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        day_stats = df.groupby('day_of_week')['mood_level'].agg(['mean', 'count']).to_dict()
        
        day_analysis = {}
        for day_idx in range(7):
            if day_idx in day_stats['mean']:
                day_analysis[day_names[day_idx]] = {
                    'avg_mood': float(day_stats['mean'][day_idx]),
                    'count': int(day_stats['count'][day_idx])
                }
        
        return day_analysis
    
    def _generate_mood_recommendations(self, df: pd.DataFrame) -> List[str]:
        """Generate mood-based recommendations"""
        recommendations = []
        
        avg_mood = df['mood_level'].mean()
        volatility = df['mood_level'].std()
        
        if avg_mood < 3:
            recommendations.append("Your average mood is below neutral. Consider activities that boost your mood.")
        
        if volatility > 1.5:
            recommendations.append("Your mood shows high variability. Try to identify triggers for mood changes.")
        
        # Day of week recommendations
        day_stats = df.groupby('day_of_week')['mood_level'].mean()
        if len(day_stats) > 1:
            worst_day = day_stats.idxmin()
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            recommendations.append(f"Your mood tends to be lowest on {day_names[worst_day]}s. Plan mood-boosting activities for this day.")
        
        return recommendations
    
    def _calculate_habit_completion_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate habit completion statistics"""
        completion_rate = float(df['completed'].mean() * 100)
        total_days = len(df)
        completed_days = int(df['completed'].sum())
        
        return {
            'completion_rate': completion_rate,
            'total_days': total_days,
            'completed_days': completed_days,
            'missed_days': total_days - completed_days
        }
    
    def _analyze_habit_streaks(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze habit streaks"""
        # Calculate streaks
        df['streak_group'] = (df['completed'] != df['completed'].shift()).cumsum()
        streaks = df[df['completed'] == 1].groupby('streak_group').size()
        
        if len(streaks) == 0:
            return {'longest_streak': 0, 'current_streak': 0, 'avg_streak': 0}
        
        longest_streak = int(streaks.max())
        avg_streak = float(streaks.mean())
        
        # Calculate current streak (from the end)
        current_streak = 0
        for i in range(len(df) - 1, -1, -1):
            if df.iloc[i]['completed'] == 1:
                current_streak += 1
            else:
                break
        
        return {
            'longest_streak': longest_streak,
            'current_streak': current_streak,
            'avg_streak': avg_streak,
            'total_streaks': len(streaks)
        }
    
    def _detect_habit_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect patterns in habit completion"""
        patterns = {}
        
        # Weekly patterns
        weekly_completion = df.groupby('day_of_week')['completed'].mean()
        patterns['weekly'] = {
            'best_day': int(weekly_completion.idxmax()),
            'worst_day': int(weekly_completion.idxmin()),
            'consistency': float(1 - weekly_completion.std())  # Higher is more consistent
        }
        
        return patterns
    
    def _analyze_habit_day_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze habit completion by day of week"""
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        day_stats = df.groupby('day_of_week')['completed'].agg(['mean', 'count']).to_dict()
        
        day_analysis = {}
        for day_idx in range(7):
            if day_idx in day_stats['mean']:
                day_analysis[day_names[day_idx]] = {
                    'completion_rate': float(day_stats['mean'][day_idx] * 100),
                    'count': int(day_stats['count'][day_idx])
                }
        
        return day_analysis
    
    def _generate_habit_recommendations(self, df: pd.DataFrame, habit_name: str) -> List[str]:
        """Generate habit-specific recommendations"""
        recommendations = []
        
        completion_rate = df['completed'].mean() * 100
        
        if completion_rate < 50:
            recommendations.append(f"Your {habit_name} completion rate is low. Consider making the habit easier or more rewarding.")
        elif completion_rate < 80:
            recommendations.append(f"You're doing well with {habit_name}. Try to identify what helps you succeed and do more of it.")
        
        # Day-specific recommendations
        day_stats = df.groupby('day_of_week')['completed'].mean()
        if len(day_stats) > 1:
            worst_day = day_stats.idxmin()
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            if day_stats[worst_day] < 0.5:
                recommendations.append(f"You struggle with {habit_name} on {day_names[worst_day]}s. Plan extra support for this day.")
        
        return recommendations
    
    def _calculate_mood_habit_correlations(self, df: pd.DataFrame, habits) -> Dict[str, Any]:
        """Calculate correlations between mood and habit completion"""
        correlations = {}
        
        for habit in habits:
            habit_col = f'habit_{habit.id}'
            if habit_col in df.columns:
                # Pearson correlation
                pearson_corr, pearson_p = pearsonr(df['mood_level'], df[habit_col])
                
                # Spearman correlation (rank-based, more robust)
                spearman_corr, spearman_p = spearmanr(df['mood_level'], df[habit_col])
                
                correlations[habit.name] = {
                    'pearson_correlation': float(pearson_corr),
                    'pearson_p_value': float(pearson_p),
                    'spearman_correlation': float(spearman_corr),
                    'spearman_p_value': float(spearman_p),
                    'significance': 'significant' if min(pearson_p, spearman_p) < 0.05 else 'not_significant',
                    'strength': self._classify_correlation_strength(abs(max(pearson_corr, spearman_corr)))
                }
        
        return correlations
    
    def _classify_correlation_strength(self, correlation: float) -> str:
        """Classify correlation strength"""
        if correlation < 0.1:
            return 'negligible'
        elif correlation < 0.3:
            return 'weak'
        elif correlation < 0.5:
            return 'moderate'
        elif correlation < 0.7:
            return 'strong'
        else:
            return 'very_strong'
    
    def _detect_correlation_patterns(self, df: pd.DataFrame, habits) -> Dict[str, Any]:
        """Detect patterns in mood-habit correlations"""
        patterns = {}
        
        # Find habits that correlate with better mood
        positive_habits = []
        negative_habits = []
        
        for habit in habits:
            habit_col = f'habit_{habit.id}'
            if habit_col in df.columns:
                corr, p_value = pearsonr(df['mood_level'], df[habit_col])
                if p_value < 0.05:  # Significant correlation
                    if corr > 0.2:
                        positive_habits.append({'name': habit.name, 'correlation': float(corr)})
                    elif corr < -0.2:
                        negative_habits.append({'name': habit.name, 'correlation': float(corr)})
        
        patterns['mood_boosting_habits'] = positive_habits
        patterns['mood_dampening_habits'] = negative_habits
        
        return patterns
    
    def _generate_correlation_insights(self, correlations: Dict, patterns: Dict) -> List[str]:
        """Generate insights from correlation analysis"""
        insights = []
        
        if patterns.get('mood_boosting_habits'):
            habit_names = [h['name'] for h in patterns['mood_boosting_habits']]
            insights.append(f"These habits correlate with better mood: {', '.join(habit_names)}")
        
        if patterns.get('mood_dampening_habits'):
            habit_names = [h['name'] for h in patterns['mood_dampening_habits']]
            insights.append(f"These habits may correlate with lower mood: {', '.join(habit_names)}")
        
        # Find strongest correlations
        strong_correlations = []
        for habit_name, corr_data in correlations.items():
            if corr_data['strength'] in ['strong', 'very_strong'] and corr_data['significance'] == 'significant':
                strong_correlations.append(habit_name)
        
        if strong_correlations:
            insights.append(f"Strong mood-habit relationships found with: {', '.join(strong_correlations)}")
        
        return insights
    
    def _assess_correlation_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess the quality of data for correlation analysis"""
        return {
            'sample_size': len(df),
            'data_quality': 'good' if len(df) >= 14 else 'limited' if len(df) >= 7 else 'insufficient',
            'completeness': float(df.notna().all(axis=1).mean() * 100)
        }
    
    def _empty_mood_analysis(self) -> Dict[str, Any]:
        """Return empty mood analysis structure"""
        return {
            'basic_stats': {'mean': 0, 'count': 0},
            'trends': {'trend': 'no_data'},
            'patterns': {},
            'volatility': {'volatility': 0, 'stability_score': 0},
            'day_of_week_analysis': {},
            'recommendations': ['No mood data available for analysis.']
        }
    
    def _empty_habit_analysis(self) -> Dict[str, Any]:
        """Return empty habit analysis structure"""
        return {}
    
    def _empty_correlation_analysis(self) -> Dict[str, Any]:
        """Return empty correlation analysis structure"""
        return {
            'correlations': {},
            'patterns': {},
            'insights': ['Insufficient data for correlation analysis.'],
            'data_quality': {'sample_size': 0, 'data_quality': 'insufficient'}
        }


class DataAggregator:
    """
    Utility class for aggregating mood and habit data for analysis
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + '.DataAggregator')
        self.django_available = False
        self.django_imports = {}
        self._check_django_availability()
    
    def _check_django_availability(self) -> None:
        """Check if Django is available and properly configured"""
        try:
            success, imports, error = _safe_django_import()
            if success:
                self.django_available = True
                self.django_imports = imports
                self.logger.info("Django components loaded successfully for DataAggregator")
            else:
                self.django_available = False
                self.logger.warning(f"Django not available for DataAggregator: {error}")
        except Exception as e:
            self.django_available = False
            self.logger.error(f"Error checking Django availability in DataAggregator: {e}")
    
    def get_user_mood_data(self, user, days: int = 30) -> pd.DataFrame:
        """
        Get user's mood data as a pandas DataFrame
        
        Args:
            user: Django User instance
            days: Number of days to retrieve
            
        Returns:
            pandas DataFrame with mood data
        """
        if not self.django_available:
            return pd.DataFrame()
        
        try:
            MoodEntry = self.django_imports['MoodEntry']
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days-1)
            
            mood_entries = MoodEntry.objects.filter(
                user=user,
                date__range=[start_date, end_date]
            ).order_by('date')
        except Exception as e:
            self.logger.error(f"Error accessing mood data: {e}")
            return pd.DataFrame()
        
        data = []
        for entry in mood_entries:
            data.append({
                'date': entry.date,
                'mood_level': entry.mood_level,
                'mood_label': entry.mood_label,
                'notes': entry.notes,
                'day_of_week': entry.date.weekday(),
                'week_of_year': entry.date.isocalendar()[1],
                'month': entry.date.month,
                'is_weekend': entry.date.weekday() >= 5
            })
        
        return pd.DataFrame(data)
    
    def get_user_habit_data(self, user, days: int = 30) -> Dict[str, pd.DataFrame]:
        """
        Get user's habit data as pandas DataFrames
        
        Args:
            user: Django User instance
            days: Number of days to retrieve
            
        Returns:
            Dictionary mapping habit names to DataFrames
        """
        if not self.django_available:
            return {}
        
        try:
            Habit = self.django_imports['Habit']
            HabitLog = self.django_imports['HabitLog']
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days-1)
            
            habits = Habit.objects.filter(user=user, is_active=True)
            habit_data = {}
        except Exception as e:
            self.logger.error(f"Error accessing habit data: {e}")
            return {}
        
        for habit in habits:
            try:
                logs = HabitLog.objects.filter(
                    habit=habit,
                    date__range=[start_date, end_date]
                ).order_by('date')
            except Exception as e:
                self.logger.error(f"Error accessing habit logs for {habit.name}: {e}")
                continue
            
            # Create complete date range
            data = []
            current_date = start_date
            log_lookup = {log.date: log for log in logs}
            
            while current_date <= end_date:
                log = log_lookup.get(current_date)
                data.append({
                    'date': current_date,
                    'completed': log.completed if log else False,
                    'notes': log.notes if log else '',
                    'day_of_week': current_date.weekday(),
                    'week_of_year': current_date.isocalendar()[1],
                    'month': current_date.month,
                    'is_weekend': current_date.weekday() >= 5
                })
                current_date += timedelta(days=1)
            
            habit_data[habit.name] = pd.DataFrame(data)
        
        return habit_data
    
    def get_combined_data(self, user, days: int = 30) -> pd.DataFrame:
        """
        Get combined mood and habit data for correlation analysis
        
        Args:
            user: Django User instance
            days: Number of days to retrieve
            
        Returns:
            pandas DataFrame with combined data
        """
        mood_df = self.get_user_mood_data(user, days)
        habit_data = self.get_user_habit_data(user, days)
        
        if mood_df.empty:
            return pd.DataFrame()
        
        # Start with mood data
        combined_df = mood_df.copy()
        
        # Add habit completion data
        for habit_name, habit_df in habit_data.items():
            if not habit_df.empty:
                # Merge on date
                habit_completion = habit_df.set_index('date')['completed']
                combined_df = combined_df.set_index('date').join(
                    habit_completion.rename(f'habit_{habit_name}'),
                    how='left'
                ).reset_index()
                
                # Fill missing values with False (not completed)
                combined_df[f'habit_{habit_name}'] = combined_df[f'habit_{habit_name}'].fillna(False)
        
        return combined_df
    
    def calculate_summary_statistics(self, user, days: int = 30) -> Dict[str, Any]:
        """
        Calculate summary statistics for user's data
        
        Args:
            user: Django User instance
            days: Number of days to analyze
            
        Returns:
            Dictionary with summary statistics
        """
        mood_df = self.get_user_mood_data(user, days)
        habit_data = self.get_user_habit_data(user, days)
        
        summary = {
            'period': {
                'days': days,
                'start_date': (date.today() - timedelta(days=days-1)).isoformat(),
                'end_date': date.today().isoformat()
            },
            'mood': {
                'total_entries': len(mood_df),
                'data_completeness': len(mood_df) / days * 100 if days > 0 else 0
            },
            'habits': {
                'total_habits': len(habit_data),
                'habit_names': list(habit_data.keys())
            }
        }
        
        if not mood_df.empty:
            summary['mood'].update({
                'average_mood': float(mood_df['mood_level'].mean()),
                'mood_range': {
                    'min': int(mood_df['mood_level'].min()),
                    'max': int(mood_df['mood_level'].max())
                },
                'volatility': float(mood_df['mood_level'].std())
            })
        
        # Add habit completion rates
        habit_completion_rates = {}
        for habit_name, habit_df in habit_data.items():
            if not habit_df.empty:
                completion_rate = habit_df['completed'].mean() * 100
                habit_completion_rates[habit_name] = float(completion_rate)
        
        summary['habits']['completion_rates'] = habit_completion_rates
        
        return summary