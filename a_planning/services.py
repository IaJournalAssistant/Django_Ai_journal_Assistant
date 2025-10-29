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
        self.webhook_url = "http://192.168.1.42:5678/webhook-test/e5769f85-68ad-42df-9ba6-48db6430ace2"
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
            return response.json() if response.content else {"status": "success"}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"n8n webhook request failed: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse n8n response: {str(e)}")
            return None
    
    def summarize_tasks(self, tasks: List[Dict[str, Any]]) -> Optional[str]:
        """Generate AI summary of tasks"""
        if not tasks:
            return None
            
        # Prepare task data for AI analysis
        task_data = []
        for task in tasks:
            task_data.append({
                'title': task.get('title', ''),
                'description': task.get('description', ''),
                'status': task.get('status', ''),
                'priority': task.get('priority', ''),
                'due_date': str(task.get('due_date', '')) if task.get('due_date') else None,
                'project': task.get('project_title', '') if task.get('project_title') else None
            })
        
        payload = {
            'action': 'summarize_tasks',
            'data': {
                'tasks': task_data,
                'count': len(task_data)
            },
            'prompt': f"Please provide a concise summary of these {len(task_data)} tasks, highlighting key priorities, upcoming deadlines, and overall progress status."
        }
        
        response = self._send_webhook_request(payload)
        if response and 'summary' in response:
            return response['summary']
        elif response and 'message' in response:
            return response['message']
        
        return None
    
    def analyze_project_progress(self, project: Dict[str, Any], tasks: List[Dict[str, Any]]) -> Optional[str]:
        """Generate AI analysis of project progress"""
        task_data = []
        for task in tasks:
            task_data.append({
                'title': task.get('title', ''),
                'status': task.get('status', ''),
                'priority': task.get('priority', ''),
                'due_date': str(task.get('due_date', '')) if task.get('due_date') else None
            })
        
        payload = {
            'action': 'analyze_project',
            'data': {
                'project': {
                    'title': project.get('title', ''),
                    'description': project.get('description', ''),
                    'progress_percentage': project.get('progress_percentage', 0),
                    'status': project.get('status', ''),
                    'target_date': str(project.get('target_completion_date', '')) if project.get('target_completion_date') else None
                },
                'tasks': task_data,
                'task_count': len(task_data)
            },
            'prompt': f"Analyze this project's progress and provide insights on completion likelihood, potential risks, and recommendations for improvement."
        }
        
        response = self._send_webhook_request(payload)
        if response and 'analysis' in response:
            return response['analysis']
        elif response and 'message' in response:
            return response['message']
        
        return None
    
    def suggest_task_breakdown(self, task_title: str, task_description: str = "") -> Optional[List[str]]:
        """Get AI suggestions for breaking down a complex task"""
        payload = {
            'action': 'suggest_subtasks',
            'data': {
                'title': task_title,
                'description': task_description
            },
            'prompt': f"Break down this task into smaller, actionable subtasks. Provide 3-5 specific, manageable steps."
        }
        
        response = self._send_webhook_request(payload)
        if response and 'suggestions' in response:
            return response['suggestions']
        elif response and 'subtasks' in response:
            return response['subtasks']
        elif response and 'message' in response:
            # Try to parse suggestions from message
            message = response['message']
            if '\n' in message:
                return [line.strip('- ').strip() for line in message.split('\n') if line.strip()]
        
        return None
    
    def generate_goal_action_plan(self, goal: Dict[str, Any]) -> Optional[str]:
        """Generate AI-powered action plan for achieving a goal"""
        payload = {
            'action': 'create_action_plan',
            'data': {
                'title': goal.get('title', ''),
                'description': goal.get('description', ''),
                'success_criteria': goal.get('success_criteria', ''),
                'target_date': str(goal.get('target_date', '')) if goal.get('target_date') else None,
                'current_progress': goal.get('progress_percentage', 0)
            },
            'prompt': f"Create a detailed action plan to achieve this goal, including specific steps, milestones, and timeline recommendations."
        }
        
        response = self._send_webhook_request(payload)
        if response and 'action_plan' in response:
            return response['action_plan']
        elif response and 'plan' in response:
            return response['plan']
        elif response and 'message' in response:
            return response['message']
        
        return None
    
    def analyze_productivity_patterns(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Analyze user's productivity patterns and provide insights"""
        payload = {
            'action': 'analyze_productivity',
            'data': user_data,
            'prompt': "Analyze the user's task completion patterns, identify productivity trends, and provide personalized recommendations for improvement."
        }
        
        response = self._send_webhook_request(payload)
        if response and 'insights' in response:
            return response['insights']
        elif response and 'analysis' in response:
            return response['analysis']
        elif response and 'message' in response:
            return response['message']
        
        return None


# Global service instance
ai_service = N8nAIService()