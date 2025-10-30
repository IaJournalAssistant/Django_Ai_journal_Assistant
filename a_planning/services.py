"""
AI Services for the Planning module using n8n webhook integration
"""
import requests
import json
import logging
from django.conf import settings
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class N8nAIService:
    """Service to interact with n8n AI workflow via webhook"""
    
    def __init__(self):
        self.webhook_url = "https://aymen2025aymen25.app.n8n.cloud/webhook-test/django-ai"
        self.timeout = 30  # 30 seconds timeout
    
    def _send_webhook_request(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send data to n8n webhook and return response"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Django-Planning-App/1.0'
            }
            
            response = requests.post(
                self.webhook_url,
                json=data,
                headers=headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            # Handle different response types
            if response.content:
                try:
                    return response.json()
                except json.JSONDecodeError:
                    # If JSON parsing fails, return the text as a message
                    return {"message": response.text}
            else:
                return {"status": "success"}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"n8n webhook request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in webhook request: {str(e)}")
            return None
    
    def _extract_ai_response(self, response: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extract AI response from various possible response formats"""
        if not response:
            return None
            
        # Handle different response structures from n8n
        if isinstance(response, dict):
            # Special handling for OpenAI format
            if 'choices' in response and isinstance(response['choices'], list) and len(response['choices']) > 0:
                choice = response['choices'][0]
                if isinstance(choice, dict) and 'message' in choice:
                    message = choice['message']
                    if isinstance(message, dict) and 'content' in message:
                        return str(message['content']).strip()
            
            # Special handling for Claude format
            if 'content' in response and isinstance(response['content'], list) and len(response['content']) > 0:
                content_item = response['content'][0]
                if isinstance(content_item, dict) and 'text' in content_item:
                    return str(content_item['text']).strip()
            
            # Try common response field names in order of preference
            for field in ['message', 'response', 'text', 'content', 'result', 'output', 'summary', 'analysis', 'insights', 'suggestions', 'action_plan', 'plan']:
                if field in response and response[field]:
                    content = response[field]
                    # Handle nested structures
                    if isinstance(content, dict):
                        # If it's a dict, try to extract text from common fields
                        for nested_field in ['text', 'content', 'message']:
                            if nested_field in content:
                                return str(content[nested_field]).strip()
                        # If no nested text field, convert to string
                        return str(content).strip()
                    elif isinstance(content, list) and len(content) > 0:
                        # Handle list content (like Claude format)
                        first_item = content[0]
                        if isinstance(first_item, dict):
                            for nested_field in ['text', 'content', 'message']:
                                if nested_field in first_item:
                                    return str(first_item[nested_field]).strip()
                        return str(first_item).strip()
                    elif isinstance(content, str):
                        return content.strip()
                    else:
                        return str(content).strip()
            
            # If no standard fields found, try to extract any string value
            for key, value in response.items():
                if isinstance(value, str) and len(value.strip()) > 10:  # Meaningful content
                    return value.strip()
            
            # Last resort: convert entire response to string
            return str(response).strip()
            
        elif isinstance(response, str):
            return response.strip()
        else:
            return str(response).strip() if response else None
    
    def summarize_tasks(self, tasks: List[Dict[str, Any]]) -> Optional[str]:
        """Generate AI summary of tasks"""
        if not tasks:
            return None
            
        # Prepare task data for AI analysis
        task_summaries = []
        for task in tasks:
            task_summary = f"Task: {task.get('title', 'Untitled')}"
            if task.get('description'):
                task_summary += f" - {task.get('description')}"
            task_summary += f" (Status: {task.get('status', 'unknown')}, Priority: {task.get('priority', 'medium')}"
            if task.get('due_date'):
                task_summary += f", Due: {task.get('due_date')}"
            if task.get('project_title'):
                task_summary += f", Project: {task.get('project_title')}"
            task_summary += ")"
            task_summaries.append(task_summary)
        
        # Create a comprehensive prompt for task summarization
        tasks_text = "\n".join(task_summaries)
        prompt = f"""TASK ANALYSIS REQUEST

Current Workload Overview ({len(tasks)} total tasks):
{tasks_text}

Please provide a strategic analysis that includes:

**Current Status Assessment:**
- Overall workload evaluation and progress distribution
- Immediate attention items and critical priorities

**Key Insights:**
- Most critical tasks requiring focus
- Potential scheduling conflicts or bottlenecks
- Workload balance assessment

**Actionable Recommendations:**
- Priority adjustments needed
- Time management suggestions for maximum productivity
- Next steps to optimize daily workflow

**Urgent Items:**
- Tasks approaching deadlines
- High-priority items that may be at risk
- Dependencies that could cause delays

Focus on practical advice that helps optimize workflow and ensures important deadlines are met. Keep response under 200 words."""
        
        payload = {"prompt": prompt}
        
        response = self._send_webhook_request(payload)
        return self._extract_ai_response(response)
    
    def analyze_project_progress(self, project: Dict[str, Any], tasks: List[Dict[str, Any]]) -> Optional[str]:
        """Generate AI analysis of project progress"""
        # Build project description
        project_info = f"Project: {project.get('title', 'Untitled Project')}"
        if project.get('description'):
            project_info += f"\nDescription: {project.get('description')}"
        project_info += f"\nProgress: {project.get('progress_percentage', 0)}%"
        project_info += f"\nStatus: {project.get('status', 'unknown')}"
        if project.get('target_completion_date'):
            project_info += f"\nTarget Completion: {project.get('target_completion_date')}"
        
        # Build tasks summary
        task_summaries = []
        for task in tasks:
            task_summary = f"- {task.get('title', 'Untitled')} ({task.get('status', 'unknown')}, {task.get('priority', 'medium')} priority)"
            if task.get('due_date'):
                task_summary += f" - Due: {task.get('due_date')}"
            task_summaries.append(task_summary)
        
        tasks_text = "\n".join(task_summaries) if task_summaries else "No tasks found"
        
        prompt = f"""PROJECT HEALTH ANALYSIS

Project Details:
{project_info}

Task Breakdown ({len(tasks)} tasks):
{tasks_text}

Please provide a comprehensive project assessment:

**Project Health Score:**
- Current progress evaluation vs. timeline
- Task completion velocity and effectiveness

**Risk Assessment:**
- Potential blockers or bottlenecks identified
- Timeline feasibility for target completion
- Critical dependencies and constraints

**Strategic Recommendations:**
- Immediate actions to improve progress
- Task prioritization adjustments needed
- Resource optimization suggestions

**Success Factors:**
- What's working well in this project
- Momentum areas to leverage and build upon

**Timeline Optimization:**
- Realistic completion projections
- Milestone adjustments if needed
- Buffer time recommendations

Provide specific, actionable insights that help ensure project success and on-time delivery. Keep under 250 words."""
        
        payload = {"prompt": prompt}
        
        response = self._send_webhook_request(payload)
        return self._extract_ai_response(response)
    
    def suggest_task_breakdown(self, task_title: str, task_description: str = "") -> Optional[str]:
        """Get AI suggestions for breaking down a complex task"""
        prompt = f"""TASK DECOMPOSITION REQUEST

Complex Task: "{task_title}"
{f'Context: {task_description}' if task_description else ''}

Please break this down into 3-5 manageable subtasks that:

**Subtask Requirements:**
- Each completable in 1-4 hours
- Clear, specific action items (not vague goals)
- Logical sequence building toward completion
- Measurable outcomes for each step

**Format each subtask as:**
- Clear action verb + specific deliverable
- Include dependencies or prerequisites if relevant
- Brief time/effort estimate when helpful

**Consider:**
- What preparation or research is needed first?
- What are the core execution steps?
- What validation or review steps are required?
- Any dependencies on other people/resources?

Provide practical subtasks that make this complex task feel manageable and create clear progress milestones."""
        
        payload = {"prompt": prompt}
        
        response = self._send_webhook_request(payload)
        return self._extract_ai_response(response)
    
    def generate_goal_action_plan(self, goal: Dict[str, Any]) -> Optional[str]:
        """Generate AI-powered action plan for achieving a goal"""
        goal_info = f"Goal: {goal.get('title', 'Untitled Goal')}"
        if goal.get('description'):
            goal_info += f"\nDescription: {goal.get('description')}"
        if goal.get('success_criteria'):
            goal_info += f"\nSuccess Criteria: {goal.get('success_criteria')}"
        goal_info += f"\nCurrent Progress: {goal.get('progress_percentage', 0)}%"
        if goal.get('target_date'):
            goal_info += f"\nTarget Date: {goal.get('target_date')}"
        
        prompt = f"""GOAL ACHIEVEMENT STRATEGY

Goal Information:
{goal_info}

Create a comprehensive action plan that includes:

**Strategic Approach:**
- Key phases or milestones to reach this goal
- Critical success factors and requirements
- Potential obstacles and mitigation strategies

**Actionable Steps:**
- Specific, time-bound actions to take
- Sequence and dependencies between steps
- Resource requirements for each phase

**Timeline Framework:**
- Realistic milestone dates with current progress considered
- Buffer time for unexpected challenges
- Progress checkpoints and review periods

**Success Metrics:**
- How to measure progress along the way
- Key indicators that you're on track
- Warning signs that adjustments are needed

**Motivation & Accountability:**
- Ways to maintain momentum toward achievement
- Accountability measures or support systems
- Celebration milestones for sustained motivation

Focus on creating a realistic, achievable roadmap that transforms this goal from aspiration into systematic execution. Keep under 300 words."""
        
        payload = {"prompt": prompt}
        
        response = self._send_webhook_request(payload)
        return self._extract_ai_response(response)
    
    def analyze_productivity_patterns(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Analyze user's productivity patterns and provide insights"""
        stats_summary = f"""Productivity Statistics:
- Total Tasks: {user_data.get('total_tasks', 0)}
- Completed Tasks: {user_data.get('completed_tasks', 0)}
- Overdue Tasks: {user_data.get('overdue_tasks', 0)}
- Task Completion Rate: {user_data.get('task_completion_rate', 0)}%
- Active Projects: {user_data.get('active_projects', 0)}
- Completed Projects: {user_data.get('completed_projects', 0)}
- Project Completion Rate: {user_data.get('project_completion_rate', 0)}%
- Active Goals: {user_data.get('active_goals', 0)}
- Achieved Goals: {user_data.get('achieved_goals', 0)}
- Goal Achievement Rate: {user_data.get('goal_achievement_rate', 0)}%"""
        
        prompt = f"""PRODUCTIVITY PATTERN ANALYSIS

Performance Metrics:
{stats_summary}

Please analyze these patterns and provide insights:

**Productivity Assessment:**
- Overall performance evaluation across tasks/projects/goals
- Strengths in current workflow and habits
- Areas showing room for improvement

**Pattern Recognition:**
- Completion rate trends and what they indicate
- Workload distribution effectiveness
- Time management patterns observed

**Optimization Opportunities:**
- Specific bottlenecks to address immediately
- Workflow improvements to implement
- Habit changes that could boost productivity

**Strategic Recommendations:**
- Priority management adjustments
- Time allocation optimization strategies
- Goal-setting refinements for better outcomes

**Action Plan:**
- 3 immediate changes to implement this week
- Longer-term productivity improvements to work toward
- Key metrics to track for continued optimization

Provide personalized advice based on these specific metrics, focusing on practical improvements that fit into daily workflow. Keep under 250 words."""
        
        payload = {"prompt": prompt}
        
        response = self._send_webhook_request(payload)
        return self._extract_ai_response(response)


# Global service instance
ai_service = N8nAIService()