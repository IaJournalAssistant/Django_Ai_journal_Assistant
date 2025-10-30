#!/usr/bin/env python
"""
Test script for n8n webhook integration
Tests the task summarization functionality
"""

import requests
import json

# Your n8n webhook URL
url = "https://aymen2025aymen25.app.n8n.cloud/webhook-test/django-ai"

# Sample task data for testing
sample_tasks = [
    {
        'title': 'Complete project proposal',
        'description': 'Write and review the Q4 project proposal document',
        'status': 'in_progress',
        'priority': 'high',
        'due_date': '2024-12-15',
        'project_title': 'Q4 Planning'
    },
    {
        'title': 'Review team feedback',
        'description': 'Go through all team feedback from last sprint',
        'status': 'pending',
        'priority': 'medium',
        'due_date': '2024-12-10',
        'project_title': 'Team Management'
    },
    {
        'title': 'Update website content',
        'description': 'Refresh the about page and add new testimonials',
        'status': 'pending',
        'priority': 'low',
        'due_date': '2024-12-20',
        'project_title': 'Website Maintenance'
    }
]

# Create task summaries
task_summaries = []
for task in sample_tasks:
    task_summary = f"Task: {task['title']}"
    if task['description']:
        task_summary += f" - {task['description']}"
    task_summary += f" (Status: {task['status']}, Priority: {task['priority']}"
    if task['due_date']:
        task_summary += f", Due: {task['due_date']}"
    if task['project_title']:
        task_summary += f", Project: {task['project_title']}"
    task_summary += ")"
    task_summaries.append(task_summary)

# Create the prompt
tasks_text = "\n".join(task_summaries)
prompt = f"""Please analyze and summarize these {len(sample_tasks)} tasks:

{tasks_text}

Provide a concise summary that includes:
1. Overall progress status
2. Key priorities and urgent items
3. Upcoming deadlines to watch
4. Any recommendations for better task management

Keep the summary under 200 words and make it actionable."""

# Prepare the payload (matching your expected format)
payload = {"prompt": prompt}

print("🧪 Testing n8n Webhook Integration")
print("=" * 50)
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("=" * 50)

try:
    # Send the request
    response = requests.post(url, json=payload, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        try:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Try to extract the AI response
            if isinstance(result, dict):
                ai_response = (result.get('summary') or 
                             result.get('message') or 
                             result.get('response') or 
                             result.get('text') or
                             str(result))
            else:
                ai_response = str(result)
            
            print("\n" + "=" * 50)
            print("🤖 AI TASK SUMMARY:")
            print("=" * 50)
            print(ai_response)
            
        except json.JSONDecodeError:
            print("✅ SUCCESS (Non-JSON Response)!")
            print(f"Response Text: {response.text}")
    else:
        print(f"❌ FAILED with status {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ REQUEST FAILED: {e}")

print("\n" + "=" * 50)
print("🏁 Test Complete!")
print("\nIf this test succeeds, your Django app should work with the AI features!")