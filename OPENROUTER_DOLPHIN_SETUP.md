# 🐬 OpenRouter + Dolphin 3.0 Mistral 24B Setup Guide

## 🎯 **Perfect Choice!**

OpenRouter with **Dolphin 3.0 Mistral 24B** is an excellent model for your planning assistant:
- ✅ **Free to use**
- ✅ **24B parameters** (very capable)
- ✅ **Good at structured responses**
- ✅ **Fast inference**
- ✅ **Reliable for planning tasks**

## 🔧 **n8n Configuration for OpenRouter**

### **1. HTTP Request Node Setup**

Instead of using OpenAI node, use **HTTP Request** node:

#### **Method**: `POST`
#### **URL**: `https://openrouter.ai/api/v1/chat/completions`

#### **Headers**:
```json
{
  "Authorization": "Bearer YOUR_OPENROUTER_API_KEY",
  "Content-Type": "application/json",
  "HTTP-Referer": "https://your-domain.com",
  "X-Title": "Django Planning Assistant"
}
```

#### **Body** (JSON):
```json
{
  "model": "cognitivecomputations/dolphin-2.9.4-llama3.1-8b:free",
  "messages": [
    {
      "role": "system",
      "content": "You are an intelligent Planning Assistant integrated into a Django-based task and project management application. Your role is to help users optimize their productivity, manage their workload effectively, and achieve their goals through actionable insights and recommendations.\n\n## Your Capabilities:\n- Analyze tasks, projects, and goals to provide strategic insights\n- Break down complex tasks into manageable subtasks\n- Create actionable plans for goal achievement\n- Identify productivity patterns and bottlenecks\n- Suggest improvements for time management and workflow optimization\n- Provide realistic timelines and milestone recommendations\n\n## Response Guidelines:\n- Keep responses concise (under 250 words unless specifically requested otherwise)\n- Focus on actionable advice and specific recommendations\n- Use a supportive, encouraging tone while being realistic about challenges\n- Prioritize urgent items and highlight potential risks\n- Reference specific tasks, projects, or goals by name when relevant\n- Provide structured responses with clear sections when appropriate\n- Avoid generic advice - tailor recommendations to the user's specific situation\n\n## Context Awareness:\nWhen analyzing user data, pay attention to:\n- Task priorities (urgent, high, medium, low) and their distribution\n- Due dates and potential deadline conflicts\n- Project progress percentages and completion rates\n- Goal achievement rates and timeline feasibility\n- Workload balance across different projects\n- Patterns in task completion and productivity metrics\n\n## Response Format:\nStructure your responses with:\n1. Brief assessment of current situation\n2. Key insights or patterns identified\n3. Specific actionable recommendations\n4. Priority items that need immediate attention\n5. Timeline suggestions when relevant\n\n## Tone:\n- Professional yet friendly\n- Encouraging and motivational\n- Realistic about challenges\n- Solution-oriented\n- Supportive of user's goals and efforts\n\nRemember: You're helping real people manage their real work and goals. Your insights should be practical, achievable, and genuinely helpful for improving their productivity and success."
    },
    {
      "role": "user",
      "content": "{{ $json.prompt }}"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 500,
  "top_p": 0.9,
  "frequency_penalty": 0.1,
  "presence_penalty": 0.1
}
```

### **2. Response Node Configuration**

#### **Simple Format (Recommended)**:
```json
{
  "message": "{{ $json.choices[0].message.content }}"
}
```

#### **Or Direct Passthrough**:
```json
{{ $json }}
```

## 🔄 **Complete n8n Workflow Structure**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Webhook       │───▶│  HTTP Request   │───▶│   Response      │
│   Trigger       │    │  (OpenRouter)   │    │   Node          │
│                 │    │                 │    │                 │
│ Path: django-ai │    │ Dolphin Model   │    │ Return JSON     │
│ Method: POST    │    │ + System Msg    │    │ with "message"  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🧪 **Test Your Setup**

### **1. Test Webhook Directly**
```bash
curl -X POST https://aymen2025aymen25.app.n8n.cloud/webhook-test/django-ai \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Analyze this task: Complete project documentation (Status: in_progress, Priority: high, Due: 2024-12-15)"}'
```

### **2. Expected Response**
```json
{
  "message": "**Current Status Assessment:**\nThis high-priority documentation task requires immediate focus given the December 15th deadline...\n\n**Key Insights:**\n- Critical project deliverable with tight timeline\n- In-progress status suggests work has begun\n- High priority indicates stakeholder importance\n\n**Actionable Recommendations:**\n- Allocate 2-3 focused hours daily until completion\n- Break documentation into sections (overview, technical specs, user guide)\n- Set daily milestones to track progress\n- Consider delegating research tasks if possible\n\n**Priority Items:**\n- Complete outline by end of week\n- Draft technical sections first (usually most time-consuming)\n- Schedule review time with stakeholders before deadline\n\nWith 2 weeks remaining, this is achievable with consistent daily effort. Focus on clarity and completeness over perfection."
}
```

## 🎯 **Dolphin 3.0 Mistral Advantages**

### **Perfect for Planning Tasks:**
- ✅ **Excellent at structured analysis**
- ✅ **Good with bullet points and sections**
- ✅ **Understands context and priorities**
- ✅ **Provides actionable recommendations**
- ✅ **Maintains consistent tone**

### **Model Characteristics:**
- **Context Length**: 32k tokens (plenty for planning data)
- **Response Quality**: High-quality, coherent responses
- **Speed**: Fast inference (good user experience)
- **Cost**: Free tier available
- **Reliability**: Stable and consistent

## 🔧 **OpenRouter API Key Setup**

### **1. Get API Key:**
1. Go to: https://openrouter.ai/
2. Sign up/login
3. Go to "Keys" section
4. Create new API key
5. Copy the key (starts with `sk-or-v1-...`)

### **2. Add to n8n:**
- In HTTP Request node headers
- Use: `Authorization: Bearer YOUR_API_KEY`

## 📊 **Model Parameters Explained**

```json
{
  "temperature": 0.7,        // Balanced creativity/consistency
  "max_tokens": 500,         // Enough for detailed responses
  "top_p": 0.9,             // Good response quality
  "frequency_penalty": 0.1,  // Reduce repetition
  "presence_penalty": 0.1    // Encourage topic diversity
}
```

## 🚀 **Testing Commands**

### **Simple Test:**
```bash
python simple_webhook_test.py
```

### **Full Task Analysis Test:**
```bash
python test_n8n_webhook.py
```

### **Django Integration Test:**
1. Go to: http://127.0.0.1:8000/planning/
2. Click "📋 Task Summary"
3. Should get intelligent Dolphin response!

## 🎉 **Expected Results**

With Dolphin 3.0 Mistral 24B, you'll get:
- **Structured responses** with clear sections
- **Actionable recommendations** tailored to your data
- **Professional tone** that's encouraging and helpful
- **Context-aware analysis** that references specific tasks/projects
- **Realistic timelines** and priority assessments
- **Consistent quality** across all AI features

## 🔧 **Troubleshooting**

### **Common Issues:**

1. **401 Unauthorized**
   - Check API key is correct
   - Verify headers format

2. **Model not found**
   - Use exact model name: `cognitivecomputations/dolphin-2.9.4-llama3.1-8b:free`
   - Check OpenRouter model availability

3. **Rate limits**
   - Free tier has limits
   - Consider upgrading for heavy usage

4. **Empty responses**
   - Check system message is included
   - Verify JSON structure

## 🎯 **Perfect Setup for Your Planning App!**

Dolphin 3.0 Mistral 24B will provide excellent AI assistance for:
- ✅ **Task prioritization and analysis**
- ✅ **Project health assessments**
- ✅ **Goal action planning**
- ✅ **Productivity pattern recognition**
- ✅ **Task breakdown and organization**

Your users will get intelligent, helpful insights that genuinely improve their productivity! 🚀