import json
import pandas as pd
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache

from .models import MoodEntry, Habit, HabitLog, AIInsight
from .ai_engine import OllamaClient, AIAnalysisEngine, StatisticalAnalyzer, DataAggregator


class OllamaClientTestCase(TestCase):
    """Test cases for OllamaClient"""
    
    def setUp(self):
        self.client = OllamaClient()
    
    def test_default_configuration(self):
        """Test that OllamaClient uses correct default configuration"""
        client = OllamaClient()
        self.assertEqual(client.base_url, "http://127.0.0.1:11434")
        self.assertEqual(client.model, "gemma3:1b")
    
    @patch('mood_tracker.ai_engine.requests.get')
    def test_check_availability_success(self, mock_get):
        """Test successful availability check"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client = OllamaClient()
        self.assertTrue(client.available)
    
    @patch('mood_tracker.ai_engine.requests.get')
    def test_check_availability_failure(self, mock_get):
        """Test availability check when service is down"""
        mock_get.side_effect = Exception("Connection refused")
        
        client = OllamaClient()
        self.assertFalse(client.available)
    
    @patch('mood_tracker.ai_engine.requests.post')
    def test_generate_insight_success(self, mock_post):
        """Test successful insight generation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'response': 'Test insight generated'}
        mock_post.return_value = mock_response
        
        self.client.available = True
        context = {'mood_data': [3, 4, 5]}
        result = self.client.generate_insight("Test prompt", context)
        
        self.assertEqual(result, 'Test insight generated')
    
    @patch('mood_tracker.ai_engine.requests.post')
    def test_generate_insight_api_error(self, mock_post):
        """Test insight generation with API error"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        self.client.available = True
        context = {'mood_data': [3, 4, 5]}
        result = self.client.generate_insight("Test prompt", context)
        
        self.assertIsNone(result)
    
    def test_generate_insight_unavailable(self):
        """Test insight generation when Ollama is unavailable"""
        self.client.available = False
        context = {'mood_data': [3, 4, 5]}
        result = self.client.generate_insight("Test prompt", context)
        
        self.assertIsNone(result)
    
    @patch('mood_tracker.ai_engine.requests.get')
    def test_check_model_availability_success(self, mock_get):
        """Test successful model availability check"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'models': [{'name': 'gemma3:1b'}, {'name': 'mistral:7b'}]
        }
        mock_get.return_value = mock_response
        
        self.client.available = True
        result = self.client.check_model_availability()
        
        self.assertTrue(result['available'])
        self.assertIn('gemma3:1b', result['models'])
    
    def test_check_model_availability_unavailable(self):
        """Test model availability check when service unavailable"""
        self.client.available = False
        result = self.client.check_model_availability()
        
        self.assertFalse(result['available'])
        self.assertEqual(result['models'], [])


class AIAnalysisEngineTestCase(TestCase):
    """Test cases for AIAnalysisEngine"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.engine = AIAnalysisEngine()
        
        # Create test data
        self.create_test_mood_data()
        self.create_test_habit_data()
        
        # Clear cache before each test
        cache.clear()
    
    def create_test_mood_data(self):
        """Create test mood entries"""
        base_date = date.today() - timedelta(days=6)
        mood_levels = [3, 4, 2, 5, 3, 4, 4]
        
        for i, mood in enumerate(mood_levels):
            MoodEntry.objects.create(
                user=self.user,
                mood_level=mood,
                mood_label='Happy' if mood >= 4 else 'Neutral',
                date=base_date + timedelta(days=i)
            )
    
    def create_test_habit_data(self):
        """Create test habit and habit logs"""
        self.habit = Habit.objects.create(
            user=self.user,
            name='Exercise',
            description='Daily exercise routine'
        )
        
        base_date = date.today() - timedelta(days=6)
        completions = [True, True, False, True, True, False, True]
        
        for i, completed in enumerate(completions):
            HabitLog.objects.create(
                habit=self.habit,
                date=base_date + timedelta(days=i),
                completed=completed
            )
    
    def test_generate_weekly_insights_with_data(self):
        """Test weekly insights generation with sufficient data"""
        insights = self.engine.generate_weekly_insights(self.user)
        
        self.assertEqual(insights['period'], 'weekly')
        self.assertIn('statistical_analysis', insights)
        self.assertIn('mood', insights['statistical_analysis'])
        self.assertIn('habits', insights['statistical_analysis'])
        self.assertIn('correlations', insights['statistical_analysis'])
        self.assertIn('recommendations', insights)
    
    def test_generate_weekly_insights_cached(self):
        """Test that weekly insights are cached properly"""
        # First call
        insights1 = self.engine.generate_weekly_insights(self.user)
        
        # Second call should return cached result
        insights2 = self.engine.generate_weekly_insights(self.user)
        
        self.assertEqual(insights1['generated_at'], insights2['generated_at'])
    
    def test_generate_weekly_insights_fallback(self):
        """Test weekly insights generation when AI is unavailable"""
        # Mock the Ollama client to be unavailable
        with patch.object(self.engine.ollama_client, 'available', False):
            insights = self.engine.generate_weekly_insights(self.user)
        
        self.assertIn('ai_insights', insights)
        # Should contain statistical insights as fallback (mood_summary, habit_summary, etc.)
        self.assertTrue(len(insights['ai_insights']) > 0)
        # Should have mood and habit summaries from statistical analysis
        self.assertIn('mood_summary', insights['ai_insights'])
        self.assertIn('habit_summary', insights['ai_insights'])
    
    def test_generate_correlation_insights(self):
        """Test correlation insights generation"""
        insights = self.engine.generate_correlation_insights(self.user, days=7)
        
        self.assertIn('correlation_analysis', insights)
        self.assertIn('correlations', insights['correlation_analysis'])
        self.assertIn('patterns', insights['correlation_analysis'])
    
    def test_generate_habit_recommendations(self):
        """Test habit-specific recommendations"""
        insights = self.engine.generate_habit_recommendations(self.user, 'Exercise', days=7)
        
        self.assertEqual(insights['habit_name'], 'Exercise')
        self.assertIn('analysis', insights)
        self.assertIn('recommendations', insights)
    
    def test_generate_habit_recommendations_not_found(self):
        """Test habit recommendations for non-existent habit"""
        insights = self.engine.generate_habit_recommendations(self.user, 'NonExistent', days=7)
        
        self.assertIn('error', insights)
    
    def test_save_insights_to_database(self):
        """Test saving insights to database"""
        insights = {
            'ai_insights': {'mood_summary': 'Test insight'},
            'recommendations': ['Test recommendation']
        }
        
        ai_insight = self.engine.save_insights_to_database(self.user, insights, 'weekly')
        
        self.assertIsNotNone(ai_insight)
        self.assertEqual(ai_insight.user, self.user)
        self.assertEqual(ai_insight.insight_type, 'weekly')
        self.assertIn('Test insight', ai_insight.content)


class StatisticalAnalyzerTestCase(TestCase):
    """Test cases for StatisticalAnalyzer"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.analyzer = StatisticalAnalyzer()
        
        # Create test data
        self.create_test_mood_data()
        self.create_test_habit_data()
    
    def create_test_mood_data(self):
        """Create test mood entries"""
        base_date = date.today() - timedelta(days=9)
        mood_levels = [3, 4, 2, 5, 3, 4, 4, 3, 5, 4]
        
        for i, mood in enumerate(mood_levels):
            MoodEntry.objects.create(
                user=self.user,
                mood_level=mood,
                mood_label='Happy' if mood >= 4 else 'Neutral',
                date=base_date + timedelta(days=i)
            )
    
    def create_test_habit_data(self):
        """Create test habit and habit logs"""
        self.habit = Habit.objects.create(
            user=self.user,
            name='Exercise',
            description='Daily exercise routine'
        )
        
        base_date = date.today() - timedelta(days=9)
        completions = [True, True, False, True, True, False, True, True, False, True]
        
        for i, completed in enumerate(completions):
            HabitLog.objects.create(
                habit=self.habit,
                date=base_date + timedelta(days=i),
                completed=completed
            )
    
    def test_analyze_mood_patterns_with_data(self):
        """Test mood pattern analysis with sufficient data"""
        analysis = self.analyzer.analyze_mood_patterns(self.user, days=10)
        
        self.assertIn('basic_stats', analysis)
        self.assertIn('trends', analysis)
        self.assertIn('patterns', analysis)
        self.assertIn('volatility', analysis)
        self.assertIn('recommendations', analysis)
        
        # Check basic stats
        self.assertGreater(analysis['basic_stats']['count'], 0)
        self.assertGreater(analysis['basic_stats']['mean'], 0)
    
    def test_analyze_mood_patterns_no_data(self):
        """Test mood pattern analysis with no data"""
        empty_user = User.objects.create_user(username='emptyuser', password='testpass')
        analysis = self.analyzer.analyze_mood_patterns(empty_user, days=10)
        
        self.assertEqual(analysis['basic_stats']['count'], 0)
        self.assertEqual(analysis['trends']['trend'], 'no_data')
    
    def test_analyze_habit_patterns_with_data(self):
        """Test habit pattern analysis with data"""
        analysis = self.analyzer.analyze_habit_patterns(self.user, days=10)
        
        self.assertIn('Exercise', analysis)
        habit_data = analysis['Exercise']
        
        self.assertIn('completion_stats', habit_data)
        self.assertIn('streaks', habit_data)
        self.assertIn('patterns', habit_data)
        self.assertIn('recommendations', habit_data)
        
        # Check completion stats
        self.assertGreater(habit_data['completion_stats']['total_days'], 0)
    
    def test_analyze_habit_patterns_no_habits(self):
        """Test habit pattern analysis with no habits"""
        empty_user = User.objects.create_user(username='emptyuser', password='testpass')
        analysis = self.analyzer.analyze_habit_patterns(empty_user, days=10)
        
        self.assertEqual(analysis, {})
    
    def test_analyze_mood_habit_correlations_with_data(self):
        """Test mood-habit correlation analysis with data"""
        analysis = self.analyzer.analyze_mood_habit_correlations(self.user, days=10)
        
        self.assertIn('correlations', analysis)
        self.assertIn('patterns', analysis)
        self.assertIn('insights', analysis)
        self.assertIn('data_quality', analysis)
        
        # Should have correlation data for Exercise habit
        if 'Exercise' in analysis['correlations']:
            exercise_corr = analysis['correlations']['Exercise']
            self.assertIn('pearson_correlation', exercise_corr)
            self.assertIn('spearman_correlation', exercise_corr)
            self.assertIn('significance', exercise_corr)
    
    def test_analyze_mood_habit_correlations_insufficient_data(self):
        """Test correlation analysis with insufficient data"""
        empty_user = User.objects.create_user(username='emptyuser', password='testpass')
        analysis = self.analyzer.analyze_mood_habit_correlations(empty_user, days=10)
        
        self.assertEqual(analysis['correlations'], {})
        self.assertIn('Insufficient data', analysis['insights'][0])
    
    def test_classify_volatility(self):
        """Test mood volatility classification"""
        self.assertEqual(self.analyzer._classify_volatility(0.3), 'very_stable')
        self.assertEqual(self.analyzer._classify_volatility(0.8), 'stable')
        self.assertEqual(self.analyzer._classify_volatility(1.2), 'moderate')
        self.assertEqual(self.analyzer._classify_volatility(1.8), 'volatile')
        self.assertEqual(self.analyzer._classify_volatility(2.5), 'very_volatile')
    
    def test_classify_correlation_strength(self):
        """Test correlation strength classification"""
        self.assertEqual(self.analyzer._classify_correlation_strength(0.05), 'negligible')
        self.assertEqual(self.analyzer._classify_correlation_strength(0.2), 'weak')
        self.assertEqual(self.analyzer._classify_correlation_strength(0.4), 'moderate')
        self.assertEqual(self.analyzer._classify_correlation_strength(0.6), 'strong')
        self.assertEqual(self.analyzer._classify_correlation_strength(0.8), 'very_strong')


class DataAggregatorTestCase(TestCase):
    """Test cases for DataAggregator"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.aggregator = DataAggregator()
        
        # Create test data
        self.create_test_data()
    
    def create_test_data(self):
        """Create test mood and habit data"""
        base_date = date.today() - timedelta(days=6)
        
        # Create mood entries
        mood_levels = [3, 4, 2, 5, 3, 4, 4]
        for i, mood in enumerate(mood_levels):
            MoodEntry.objects.create(
                user=self.user,
                mood_level=mood,
                mood_label='Happy' if mood >= 4 else 'Neutral',
                date=base_date + timedelta(days=i)
            )
        
        # Create habit and logs
        self.habit = Habit.objects.create(
            user=self.user,
            name='Exercise',
            description='Daily exercise routine'
        )
        
        completions = [True, True, False, True, True, False, True]
        for i, completed in enumerate(completions):
            HabitLog.objects.create(
                habit=self.habit,
                date=base_date + timedelta(days=i),
                completed=completed
            )
    
    def test_get_user_mood_data(self):
        """Test retrieving user mood data as DataFrame"""
        df = self.aggregator.get_user_mood_data(self.user, days=7)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        self.assertIn('mood_level', df.columns)
        self.assertIn('mood_label', df.columns)
        self.assertIn('day_of_week', df.columns)
        self.assertIn('is_weekend', df.columns)
    
    def test_get_user_mood_data_empty(self):
        """Test retrieving mood data for user with no data"""
        empty_user = User.objects.create_user(username='emptyuser', password='testpass')
        df = self.aggregator.get_user_mood_data(empty_user, days=7)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 0)
    
    def test_get_user_habit_data(self):
        """Test retrieving user habit data as DataFrames"""
        habit_data = self.aggregator.get_user_habit_data(self.user, days=7)
        
        self.assertIsInstance(habit_data, dict)
        self.assertIn('Exercise', habit_data)
        
        exercise_df = habit_data['Exercise']
        self.assertIsInstance(exercise_df, pd.DataFrame)
        self.assertEqual(len(exercise_df), 7)  # Should have 7 days of data
        self.assertIn('completed', exercise_df.columns)
        self.assertIn('day_of_week', exercise_df.columns)
    
    def test_get_user_habit_data_empty(self):
        """Test retrieving habit data for user with no habits"""
        empty_user = User.objects.create_user(username='emptyuser', password='testpass')
        habit_data = self.aggregator.get_user_habit_data(empty_user, days=7)
        
        self.assertIsInstance(habit_data, dict)
        self.assertEqual(len(habit_data), 0)
    
    def test_get_combined_data(self):
        """Test retrieving combined mood and habit data"""
        df = self.aggregator.get_combined_data(self.user, days=7)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        self.assertIn('mood_level', df.columns)
        self.assertIn('habit_Exercise', df.columns)
    
    def test_get_combined_data_no_mood(self):
        """Test combined data when user has no mood data"""
        empty_user = User.objects.create_user(username='emptyuser', password='testpass')
        df = self.aggregator.get_combined_data(empty_user, days=7)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 0)
    
    def test_calculate_summary_statistics(self):
        """Test calculating summary statistics"""
        summary = self.aggregator.calculate_summary_statistics(self.user, days=7)
        
        self.assertIn('period', summary)
        self.assertIn('mood', summary)
        self.assertIn('habits', summary)
        
        # Check period info
        self.assertEqual(summary['period']['days'], 7)
        
        # Check mood stats
        self.assertGreater(summary['mood']['total_entries'], 0)
        self.assertGreater(summary['mood']['data_completeness'], 0)
        self.assertIn('average_mood', summary['mood'])
        
        # Check habit stats
        self.assertEqual(summary['habits']['total_habits'], 1)
        self.assertIn('Exercise', summary['habits']['habit_names'])
        self.assertIn('Exercise', summary['habits']['completion_rates'])
    
    def test_calculate_summary_statistics_empty(self):
        """Test summary statistics for user with no data"""
        empty_user = User.objects.create_user(username='emptyuser', password='testpass')
        summary = self.aggregator.calculate_summary_statistics(empty_user, days=7)
        
        self.assertEqual(summary['mood']['total_entries'], 0)
        self.assertEqual(summary['habits']['total_habits'], 0)
        self.assertEqual(summary['habits']['completion_rates'], {})
