# n8n AI Integration Setup Guide

## Overview
This Django planning application now includes AI-powered features that integrate with your n8n workflow at `https://aymen2025aymen25.app.n8n.cloud`.

## AI Features Added

### 1. 🤖 AI Task Summary
- **Endpoint**: `/planning/ai/task-summary/`
- **Purpose**: Generates intelligent summaries of all user tasks
- **Location**: Planning Dashboard
- **n8n Webhook**: `POST https://aymen2025aymen25.app.n8n.cloud/webhook-test/django-ai`

### 2. 🔍 AI Project Analysis
- **Endpoint**: `/planning/ai/project-analysis/<project_id>/`
- **Purpose**: Analyzes project progress and provides insights
- **Location**: Project Detail Pages
- **n8n Webhook**: `POST https://aymen2025aymen25.app.n8n.cloud/webhook-test/django-ai`

### 3. 🎯 AI Goal Action Plan
- **Endpoint**: `/planning/ai/goal-action-plan/<goal_id>/`
- **Purpose**: Creates actionable plans for achieving goals
- **Location**: Goal Detail Pages
- **n8n Webhook**: `POST https://aymen2025aymen25.app.n8n.cloud/webhook-test/django-ai`

### 4. 🧩 AI Task Breakdown
- **Endpoint**: `/planning/ai/task-breakdown/`
- **Purpose**: Breaks down complex tasks into smaller subtasks
- **Location**: Task Creation Form
- **n8n Webhook**: `POST https://aymen2025aymen25.app.n8n.cloud/webhook-test/django-ai`

### 5. 📊 AI Productivity Insights
- **Endpoint**: `/planning/ai/productivity-insights/`
- **Purpose**: Analyzes productivity patterns and provides recommendations
- **Location**: Planning Dashboard
- **n8n Webhook**: `POST https://aymen2025aymen25.app.n8n.cloud/webhook-test/django-ai`

## n8n Workflow Setup

### Single Webhook Endpoint
All AI features now use a single webhook endpoint with different prompts:

**Webhook URL**: `https://aymen2025aymen25.app.n8n.cloud/webhook-test/django-ai`

### Request Format
All requests use the same simple format:
```json
{
  "prompt": "Your AI prompt here..."
}
```

### Expected Response
Your n8n workflow should return a JSON response with the AI-generated content:
```json
{
  "message": "AI response text here...",
  // or
  "response": "AI response text here...",
  // or
  "text": "AI response text here..."
}
```

### Required Webhooks (Legacy - for reference)
If you want to use separate endpoints, create these webhook endpoints in your n8n workflow:

1. **Task Summary Webhook**
   - URL: `http://192.168.1.42:5678/webhook/summarize-tasks`
   - Method: POST
   - Expected Input: Array of task objects
   - Expected Output: `{ "summary": "AI generated summary text" }`

2. **Project Analysis Webhook**
   - URL: `http://192.168.1.42:5678/webhook/analyze-project`
   - Method: POST
   - Expected Input: Project data + tasks array
   - Expected Output: `{ "analysis": "AI generated analysis text" }`

3. **Goal Action Plan Webhook**
   - URL: `http://192.168.1.42:5678/webhook/goal-action-plan`
   - Method: POST
   - Expected Input: Goal data object
   - Expected Output: `{ "action_plan": "AI generated action plan text" }`

4. **Task Breakdown Webhook**
   - URL: `http://192.168.1.42:5678/webhook/task-breakdown`
   - Method: POST
   - Expected Input: `{ "title": "task title", "description": "task description" }`
   - Expected Output: `{ "suggestions": "AI generated breakdown suggestions" }`

5. **Productivity Insights Webhook**
   - URL: `http://192.168.1.42:5678/webhook/productivity-insights`
   - Method: POST
   - Expected Input: User productivity statistics
   - Expected Output: `{ "insights": "AI generated productivity insights" }`

## Sample n8n Workflow Structure

```
1. Webhook Trigger (Listen for Django requests)
2. Function Node (Process input data)
3. OpenAI/Claude Node (Generate AI response)
4. Function Node (Format response)
5. Respond to Webhook (Return JSON response)
```

## Data Formats

### Task Summary Input
```json
[
  {
    "title": "Task title",
    "description": "Task description",
    "status": "pending|in_progress|completed",
    "priority": "low|medium|high|urgent",
    "due_date": "2024-12-31T23:59:59Z",
    "project_title": "Associated project name"
  }
]
```

### Project Analysis Input
```json
{
  "project_data": {
    "title": "Project name",
    "description": "Project description",
    "progress_percentage": 75,
    "status": "active|completed|on_hold|cancelled",
    "target_completion_date": "2024-12-31T23:59:59Z"
  },
  "tasks": [
    {
      "title": "Task title",
      "status": "pending|in_progress|completed",
      "priority": "low|medium|high|urgent",
      "due_date": "2024-12-31T23:59:59Z"
    }
  ]
}
```

### Goal Action Plan Input
```json
{
  "title": "Goal title",
  "description": "Goal description",
  "success_criteria": "Success criteria text",
  "target_date": "2024-12-31T23:59:59Z",
  "progress_percentage": 50
}
```

### Productivity Insights Input
```json
{
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
```

## Testing the Integration

1. **Start your n8n workflow** at `http://192.168.1.42:5678`
2. **Create the required webhook endpoints** in n8n
3. **Test each AI feature** from the Django application:
   - Go to Planning Dashboard and click "📋 Task Summary"
   - Visit a project detail page and click "🤖 AI Project Analysis"
   - Visit a goal detail page and click "🤖 AI Action Plan"
   - Create a new task and click "🤖 AI Task Breakdown"
   - Go to Planning Dashboard and click "📊 Productivity Insights"

## Error Handling

The application includes comprehensive error handling:
- Network connection errors
- n8n workflow failures
- Invalid response formats
- Missing webhook endpoints

All errors are displayed to users with helpful messages and troubleshooting tips.

## AI Insights Storage

All successful AI responses are stored in the `AIInsight` model with:
- User association
- Content text
- Insight type (task_summary, project_analysis, etc.)
- Confidence score
- Timestamp

This allows for future analysis and improvement of AI recommendations.

## Configuration

The n8n webhook URL is configured in `a_planning/services.py`:
```python
N8N_WEBHOOK_BASE_URL = "http://192.168.1.42:5678/webhook"
```

Update this URL if your n8n instance is running on a different address.