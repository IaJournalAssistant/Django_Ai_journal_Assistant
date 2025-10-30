# 🔧 n8n Workflow Setup Guide

## Complete n8n Workflow Configuration

### 1. **Webhook Node Configuration**
```json
{
  "path": "django-ai",
  "httpMethod": "POST",
  "responseMode": "responseNode",
  "options": {}
}
```

### 2. **OpenAI/Claude Node Configuration**

#### **System Message (Critical!):**
```
You are an intelligent Planning Assistant integrated into a Django-based task and project management application. Your role is to help users optimize their productivity, manage their workload effectively, and achieve their goals through actionable insights and recommendations.

## Your Capabilities:
- Analyze tasks, projects, and goals to provide strategic insights
- Break down complex tasks into manageable subtasks
- Create actionable plans for goal achievement
- Identify productivity patterns and bottlenecks
- Suggest improvements for time management and workflow optimization
- Provide realistic timelines and milestone recommendations

## Response Guidelines:
- Keep responses concise (under 250 words unless specifically requested otherwise)
- Focus on actionable advice and specific recommendations
- Use a supportive, encouraging tone while being realistic about challenges
- Prioritize urgent items and highlight potential risks
- Reference specific tasks, projects, or goals by name when relevant
- Provide structured responses with clear sections when appropriate
- Avoid generic advice - tailor recommendations to the user's specific situation

## Context Awareness:
When analyzing user data, pay attention to:
- Task priorities (urgent, high, medium, low) and their distribution
- Due dates and potential deadline conflicts
- Project progress percentages and completion rates
- Goal achievement rates and timeline feasibility
- Workload balance across different projects
- Patterns in task completion and productivity metrics

## Response Format:
Structure your responses with:
1. Brief assessment of current situation
2. Key insights or patterns identified
3. Specific actionable recommendations
4. Priority items that need immediate attention
5. Timeline suggestions when relevant

## Tone:
- Professional yet friendly
- Encouraging and motivational
- Realistic about challenges
- Solution-oriented
- Supportive of user's goals and efforts

Remember: You're helping real people manage their real work and goals. Your insights should be practical, achievable, and genuinely helpful for improving their productivity and success.
```

#### **User Message:**
```
{{ $json.prompt }}
```

#### **Model Settings:**
- **Temperature**: 0.7 (balanced creativity and consistency)
- **Max Tokens**: 500 (allows for detailed responses)
- **Top P**: 0.9 (good response quality)

### 3. **Response Node Configuration**
```json
{
  "message": "{{ $json.choices[0].message.content }}"
}
```

## Complete Workflow Structure

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Webhook       │───▶│   OpenAI/Claude │───▶│   Response      │
│   Trigger       │    │   Chat Model    │    │   Node          │
│                 │    │                 │    │                 │
│ Path: django-ai │    │ System Message  │    │ Return JSON     │
│ Method: POST    │    │ + User Prompt   │    │ with "message"  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Testing Your Workflow

### **Step 1: Test with Simple Prompt**
```json
{
  "prompt": "Analyze this task: Complete project documentation (Status: in_progress, Priority: high, Due: 2024-12-15)"
}
```

### **Step 2: Test with Complex Task Analysis**
```json
{
  "prompt": "TASK ANALYSIS REQUEST\n\nCurrent Workload Overview (3 total tasks):\nTask: Complete project proposal - Write Q4 proposal (Status: in_progress, Priority: high, Due: 2024-12-15, Project: Q4 Planning)\nTask: Review team feedback - Go through sprint feedback (Status: pending, Priority: medium, Due: 2024-12-10, Project: Team Management)\nTask: Update website - Refresh about page (Status: pending, Priority: low, Due: 2024-12-20, Project: Website)\n\nPlease provide a strategic analysis with current status, key insights, recommendations, and urgent items."
}
```

### **Expected Response Format:**
```json
{
  "message": "**Current Status Assessment:**\nYou have a well-balanced workload with 3 tasks across different projects...\n\n**Key Insights:**\n- High-priority Q4 proposal needs immediate focus...\n\n**Actionable Recommendations:**\n- Prioritize the project proposal completion by Dec 15th...\n\n**Urgent Items:**\n- Team feedback review is due in 2 days - schedule time today..."
}
```

## Workflow Activation

### **For Testing:**
1. Click "Execute workflow" button
2. Test with webhook calls
3. Check response format

### **For Production:**
1. Save the workflow
2. Toggle "Active" switch ON
3. Workflow runs continuously
4. No need to click "Execute" each time

## Troubleshooting

### **Common Issues:**

1. **"Webhook not registered"**
   - Click "Execute workflow" first
   - Make sure workflow is saved

2. **Empty responses**
   - Check system message is set
   - Verify API keys are configured
   - Check model settings (temperature, max tokens)

3. **Wrong response format**
   - Ensure Response node returns `{"message": "..."}`
   - Check JSON structure in response

### **Testing Commands:**
```bash
# Test basic connectivity
python simple_webhook_test.py

# Test full task analysis
python test_n8n_webhook.py
```

## 🎯 **Result:**
With this setup, your Django planning app will receive intelligent, contextual responses that:
- Reference specific tasks, projects, and goals by name
- Provide actionable recommendations
- Maintain consistent helpful tone
- Focus on productivity optimization
- Give realistic timelines and priorities

Your AI assistant will now be a true planning partner! 🚀