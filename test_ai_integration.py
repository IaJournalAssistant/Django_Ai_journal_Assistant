#!/usr/bin/env python
"""
Test script for n8n AI integration
Run this to test if your n8n webhooks are working correctly
"""

import requests
import json

# Configuration
N8N_BASE_URL = "http://192.168.1.42:5678/webhook"
DJANGO_BASE_URL = "http://127.0.0.1:8000"

def test_n8n_webhook(endpoint, data):
    """Test a specific n8n webhook endpoint"""
    url = f"{N8N_BASE_URL}/{endpoint}"
    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ {endpoint}: HTTP {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ {endpoint}: Connection error - {e}")
        return None

def test_all_webhooks():
    """Test all n8n webhook endpoints"""
    print("🧪 Testing n8n AI Integration Webhooks")
    print("=" * 50)
    
    # Test 1: Task Summary
    print("1. Testing Task Summary Webhook...")
    task_data = [
        {
            "title": "Complete project proposal",
            "description": "Write and review the Q4 project proposal",
            "status": "in_progress",
            "priority": "high",
            "due_date": "2024-12-15T17:00:00Z",
            "project_title": "Q4 Planning"
        },
        {
            "title": "Review team feedback",
            "description": "Go through all team feedback from last sprint",
            "status": "pending",
            "priority": "medium",
            "due_date": "2024-12-10T12:00:00Z",
            "project_title": "Team Management"
        }
    ]
    
    result = test_n8n_webhook("summarize-tasks", task_data)
    if result and "summary" in result:
        print(f"✅ Task Summary: {result['summary'][:100]}...")
    else:
        print("❌ Task Summary: Failed")
    
    # Test 2: Project Analysis
    print("\n2. Testing Project Analysis Webhook...")
    project_data = {
        "project_data": {
            "title": "Website Redesign",
            "description": "Complete redesign of company website",
            "progress_percentage": 65,
            "status": "active",
            "target_completion_date": "2024-12-31T23:59:59Z"
        },
        "tasks": [
            {
                "title": "Design mockups",
                "status": "completed",
                "priority": "high",
                "due_date": "2024-12-01T17:00:00Z"
            },
            {
                "title": "Implement frontend",
                "status": "in_progress",
                "priority": "high",
                "due_date": "2024-12-20T17:00:00Z"
            }
        ]
    }
    
    result = test_n8n_webhook("analyze-project", project_data)
    if result and "analysis" in result:
        print(f"✅ Project Analysis: {result['analysis'][:100]}...")
    else:
        print("❌ Project Analysis: Failed")
    
    # Test 3: Goal Action Plan
    print("\n3. Testing Goal Action Plan Webhook...")
    goal_data = {
        "title": "Learn Python Machine Learning",
        "description": "Master ML fundamentals and build 3 projects",
        "success_criteria": "Complete online course, build 3 ML projects, pass certification exam",
        "target_date": "2025-03-31T23:59:59Z",
        "progress_percentage": 25
    }
    
    result = test_n8n_webhook("goal-action-plan", goal_data)
    if result and "action_plan" in result:
        print(f"✅ Goal Action Plan: {result['action_plan'][:100]}...")
    else:
        print("❌ Goal Action Plan: Failed")
    
    # Test 4: Task Breakdown
    print("\n4. Testing Task Breakdown Webhook...")
    task_breakdown_data = {
        "title": "Launch new marketing campaign",
        "description": "Create and execute a comprehensive marketing campaign for our new product launch"
    }
    
    result = test_n8n_webhook("task-breakdown", task_breakdown_data)
    if result and "suggestions" in result:
        print(f"✅ Task Breakdown: {result['suggestions'][:100]}...")
    else:
        print("❌ Task Breakdown: Failed")
    
    # Test 5: Productivity Insights
    print("\n5. Testing Productivity Insights Webhook...")
    productivity_data = {
        "total_tasks": 25,
        "completed_tasks": 18,
        "overdue_tasks": 3,
        "task_completion_rate": 72.0,
        "active_projects": 5,
        "completed_projects": 2,
        "project_completion_rate": 28.6,
        "active_goals": 3,
        "achieved_goals": 1,
        "goal_achievement_rate": 25.0
    }
    
    result = test_n8n_webhook("productivity-insights", productivity_data)
    if result and "insights" in result:
        print(f"✅ Productivity Insights: {result['insights'][:100]}...")
    else:
        print("❌ Productivity Insights: Failed")
    
    print("\n" + "=" * 50)
    print("🏁 Testing Complete!")
    print("\nIf any tests failed, make sure:")
    print("1. n8n is running at http://192.168.1.42:5678")
    print("2. All webhook endpoints are configured in n8n")
    print("3. Your n8n workflow includes AI processing nodes")

if __name__ == "__main__":
    test_all_webhooks()