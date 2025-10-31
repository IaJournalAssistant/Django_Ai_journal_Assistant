"""
AI Models Integration for Planning Module
Uses existing Hugging Face models safely without affecting other modules
"""
import logging
from typing import Optional, Dict, Any, List
from transformers import pipeline
import random

logger = logging.getLogger(__name__)

# Global model instances (cached for performance)
_sentiment_pipeline = None
_text_generator = None

def get_sentiment_pipeline():
    """Get or create sentiment analysis pipeline"""
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        try:
            _sentiment_pipeline = pipeline("sentiment-analysis")
            logger.info("Sentiment analysis pipeline loaded successfully")
        except Exception as e:
            logger.error(f"Error loading sentiment pipeline: {e}")
            _sentiment_pipeline = None
    return _sentiment_pipeline

def get_text_generator():
    """Get or create text generation pipeline for planning insights"""
    global _text_generator
    if _text_generator is None:
        try:
            # Use a lightweight model for planning insights
            _text_generator = pipeline(
                "text-generation",
                model="microsoft/DialoGPT-small",
                device=-1  # CPU only to avoid conflicts
            )
            logger.info("Text generation pipeline loaded successfully")
        except Exception as e:
            logger.error(f"Error loading text generator: {e}")
            _text_generator = None
    return _text_generator

def analyze_task_sentiment(task_title: str, task_description: str = "") -> Dict[str, Any]:
    """Analyze sentiment of task content"""
    try:
        sentiment_pipeline = get_sentiment_pipeline()
        if not sentiment_pipeline:
            return {"sentiment": "NEUTRAL", "confidence": 0.5}
        
        # Combine title and description for analysis
        text = f"{task_title}. {task_description}".strip()
        if len(text) > 512:  # Truncate if too long
            text = text[:512]
        
        result = sentiment_pipeline(text)
        return {
            "sentiment": result[0]["label"],
            "confidence": result[0]["score"]
        }
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        return {"sentiment": "NEUTRAL", "confidence": 0.5}

def generate_task_insights(tasks_data: List[Dict]) -> str:
    """Generate insights about tasks using local AI"""
    try:
        if not tasks_data:
            return "No tasks to analyze."
        
        # Analyze sentiment patterns
        sentiments = []
        priorities = {"urgent": 0, "high": 0, "medium": 0, "low": 0}
        statuses = {"completed": 0, "in_progress": 0, "pending": 0}
        
        for task in tasks_data:
            # Count priorities and statuses
            priority = task.get("priority", "medium")
            status = task.get("status", "pending")
            priorities[priority] = priorities.get(priority, 0) + 1
            statuses[status] = statuses.get(status, 0) + 1
            
            # Analyze sentiment
            sentiment_result = analyze_task_sentiment(
                task.get("title", ""), 
                task.get("description", "")
            )
            sentiments.append(sentiment_result["sentiment"])
        
        # Generate insights based on analysis
        total_tasks = len(tasks_data)
        completion_rate = (statuses["completed"] / total_tasks * 100) if total_tasks > 0 else 0
        
        # Count sentiment distribution
        positive_tasks = sentiments.count("POSITIVE")
        negative_tasks = sentiments.count("NEGATIVE")
        
        insights = []
        
        # Completion insights
        if completion_rate >= 80:
            insights.append("🎉 Excellent progress! You're completing most of your tasks.")
        elif completion_rate >= 60:
            insights.append("👍 Good momentum on task completion.")
        else:
            insights.append("💪 Focus on completing pending tasks to build momentum.")
        
        # Priority insights
        if priorities["urgent"] > 3:
            insights.append("⚠️ High number of urgent tasks - consider prioritizing or delegating.")
        
        # Sentiment insights
        if negative_tasks > positive_tasks:
            insights.append("🌱 Some tasks seem challenging - break them into smaller steps.")
        elif positive_tasks > negative_tasks:
            insights.append("✨ Your tasks reflect positive energy and clear goals.")
        
        # Workload insights
        if total_tasks > 20:
            insights.append("📋 Large task list - consider focusing on top 3 priorities daily.")
        
        return "\n\n".join(insights) if insights else "Keep up the great work on your tasks!"
        
    except Exception as e:
        logger.error(f"Error generating task insights: {e}")
        return "Unable to generate insights at this time."

def generate_project_analysis(project_data: Dict, tasks_data: List[Dict]) -> str:
    """Generate project analysis using local AI"""
    try:
        project_title = project_data.get("title", "Project")
        progress = project_data.get("progress_percentage", 0)
        total_tasks = len(tasks_data)
        
        if total_tasks == 0:
            return f"Project '{project_title}' needs tasks to track progress effectively."
        
        completed_tasks = len([t for t in tasks_data if t.get("status") == "completed"])
        overdue_tasks = len([t for t in tasks_data if t.get("due_date") and "overdue" in str(t)])
        
        insights = []
        
        # Progress analysis
        if progress >= 90:
            insights.append(f"🎯 Project '{project_title}' is nearly complete! Focus on final deliverables.")
        elif progress >= 70:
            insights.append(f"📈 Strong progress on '{project_title}'. Maintain momentum.")
        elif progress >= 40:
            insights.append(f"⚡ '{project_title}' is gaining traction. Keep pushing forward.")
        else:
            insights.append(f"🚀 '{project_title}' is in early stages. Focus on key milestones.")
        
        # Task analysis
        if overdue_tasks > 0:
            insights.append(f"⏰ {overdue_tasks} overdue tasks need immediate attention.")
        
        if completed_tasks > 0:
            completion_rate = (completed_tasks / total_tasks) * 100
            insights.append(f"✅ {completion_rate:.0f}% task completion rate.")
        
        # Recommendations
        if total_tasks > 15:
            insights.append("💡 Consider breaking large tasks into smaller, manageable pieces.")
        
        return "\n\n".join(insights)
        
    except Exception as e:
        logger.error(f"Error generating project analysis: {e}")
        return f"Project '{project_data.get('title', 'Unknown')}' analysis unavailable."

def generate_goal_action_plan(goal_data: Dict) -> str:
    """Generate action plan for goals using local AI"""
    try:
        goal_title = goal_data.get("title", "Goal")
        progress = goal_data.get("progress_percentage", 0)
        target_date = goal_data.get("target_date", "")
        
        insights = []
        
        # Progress-based recommendations
        if progress >= 80:
            insights.append(f"🏆 Goal '{goal_title}' is almost achieved! Focus on final steps.")
            insights.append("✨ Celebrate small wins as you approach completion.")
        elif progress >= 50:
            insights.append(f"📊 '{goal_title}' is halfway there. Maintain consistent effort.")
            insights.append("🎯 Review what's working and double down on successful strategies.")
        elif progress >= 25:
            insights.append(f"🌱 '{goal_title}' is building momentum. Stay committed to daily actions.")
            insights.append("💪 Break remaining work into weekly milestones.")
        else:
            insights.append(f"🚀 '{goal_title}' is ready for action. Start with the smallest step today.")
            insights.append("📝 Create a clear action plan with specific, measurable steps.")
        
        # Time-based recommendations
        if target_date:
            insights.append("⏰ Set regular check-ins to track progress toward your target date.")
        
        # General action steps
        insights.extend([
            "🔄 Review progress weekly and adjust strategies as needed.",
            "🤝 Consider sharing your goal with someone for accountability.",
            "🎉 Plan how you'll celebrate when you achieve this goal."
        ])
        
        return "\n\n".join(insights)
        
    except Exception as e:
        logger.error(f"Error generating goal action plan: {e}")
        return f"Action plan for '{goal_data.get('title', 'Unknown')}' unavailable."

def generate_productivity_insights(user_data: Dict) -> str:
    """Generate productivity insights using local analysis"""
    try:
        task_completion = user_data.get("task_completion_rate", 0)
        project_completion = user_data.get("project_completion_rate", 0)
        goal_achievement = user_data.get("goal_achievement_rate", 0)
        
        insights = []
        
        # Overall assessment
        avg_performance = (task_completion + project_completion + goal_achievement) / 3
        
        if avg_performance >= 80:
            insights.append("🌟 Outstanding productivity! You're excelling across all areas.")
        elif avg_performance >= 65:
            insights.append("👍 Strong productivity patterns. You're on the right track.")
        elif avg_performance >= 50:
            insights.append("⚡ Good foundation. Focus on consistency to improve further.")
        else:
            insights.append("🌱 Building momentum. Small daily improvements lead to big results.")
        
        # Specific insights
        if task_completion >= 80:
            insights.append("✅ Excellent task completion rate. You're great at following through.")
        elif task_completion < 50:
            insights.append("📋 Focus on completing fewer tasks but finishing them consistently.")
        
        if project_completion >= 70:
            insights.append("🎯 Strong project management skills. You see things through to completion.")
        elif project_completion < 40:
            insights.append("📈 Break projects into smaller milestones for better completion rates.")
        
        if goal_achievement >= 60:
            insights.append("🏆 Great goal achievement rate. You turn aspirations into reality.")
        elif goal_achievement < 30:
            insights.append("🎯 Set smaller, more achievable goals to build success momentum.")
        
        # Actionable recommendations
        insights.extend([
            "💡 Tip: Focus on your top 3 priorities each day for maximum impact.",
            "🔄 Regular weekly reviews help maintain momentum and adjust strategies.",
            "🎉 Celebrate completed tasks and projects to maintain motivation."
        ])
        
        return "\n\n".join(insights)
        
    except Exception as e:
        logger.error(f"Error generating productivity insights: {e}")
        return "Productivity analysis unavailable at this time."