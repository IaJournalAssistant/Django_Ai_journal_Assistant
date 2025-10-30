# 🔧 n8n Response Node Configurations

## Supported Response Formats

Your Django AI service now handles **any** response format from n8n. Here are the most common configurations:

## 1. **Simple Response Node (Recommended)**

### Configuration:
```json
{
  "message": "{{ $json.choices[0].message.content }}"
}
```

### What Django Receives:
```json
{
  "message": "**Current Status Assessment:**\nYou have 3 tasks with mixed priorities..."
}
```

### ✅ **Best for**: Most use cases, simple setup

---

## 2. **Direct OpenAI Passthrough**

### Configuration:
```json
{{ $json }}
```

### What Django Receives:
```json
{
  "choices": [
    {
      "message": {
        "content": "**Project Health Score:**\nYour project is performing well..."
      }
    }
  ]
}
```

### ✅ **Best for**: When you want to preserve full OpenAI response structure

---

## 3. **Claude Response Format**

### Configuration:
```json
{
  "content": [
    {
      "text": "{{ $json.content[0].text }}"
    }
  ]
}
```

### What Django Receives:
```json
{
  "content": [
    {
      "text": "**Productivity Assessment:**\nYour completion rates show..."
    }
  ]
}
```

### ✅ **Best for**: Claude API integration

---

## 4. **Custom Response Fields**

### Configuration:
```json
{
  "analysis": "{{ $json.choices[0].message.content }}",
  "timestamp": "{{ $now }}",
  "model": "gpt-4"
}
```

### What Django Receives:
```json
{
  "analysis": "**Strategic Recommendations:**\nFocus on high-priority items...",
  "timestamp": "2024-10-30T12:00:00Z",
  "model": "gpt-4"
}
```

### ✅ **Best for**: When you need additional metadata

---

## 5. **Multiple Response Types**

### Configuration:
```json
{
  "summary": "{{ $json.choices[0].message.content }}",
  "insights": "{{ $json.choices[0].message.content }}",
  "recommendations": "{{ $json.choices[0].message.content }}"
}
```

### What Django Receives:
```json
{
  "summary": "Task analysis content...",
  "insights": "Key insights content...", 
  "recommendations": "Action items..."
}
```

### ✅ **Best for**: Different AI functions using same workflow

---

## 6. **Plain Text Response**

### Configuration:
```
{{ $json.choices[0].message.content }}
```

### What Django Receives:
```
"**Current Status Assessment:**\nYou have a balanced workload..."
```

### ✅ **Best for**: Minimal setup, text-only responses

---

## Response Field Priority

The Django service checks fields in this order:

1. `message` ⭐ **Most Common**
2. `response`
3. `text`
4. `content`
5. `result`
6. `output`
7. `summary`
8. `analysis`
9. `insights`
10. `suggestions`
11. `action_plan`
12. `plan`

## Error Handling

### If n8n Returns Error:
```json
{
  "error": "AI model unavailable",
  "code": 503
}
```

### Django Response:
- Logs the error
- Returns `None` to trigger fallback message
- User sees: "Failed to generate AI response. Please check your n8n workflow."

## Testing Your Configuration

### 1. **Test with Simple Prompt:**
```bash
python simple_webhook_test.py
```

### 2. **Test Response Extraction:**
```bash
python test_response_formats.py
```

### 3. **Test in Django:**
1. Go to: http://127.0.0.1:8000/planning/
2. Click "📋 Task Summary"
3. Check browser network tab for response format

## Recommended Setup

### **For Beginners:**
```json
{
  "message": "{{ $json.choices[0].message.content }}"
}
```

### **For Advanced Users:**
```json
{
  "message": "{{ $json.choices[0].message.content }}",
  "model": "{{ $json.model }}",
  "tokens": "{{ $json.usage.total_tokens }}",
  "timestamp": "{{ $now }}"
}
```

## 🎯 **Result:**

No matter how you configure your n8n response node, Django will extract the AI content correctly! The system is designed to be flexible and handle any response format you choose. 🚀

## Quick Setup Checklist:

✅ **Webhook node**: Path = `django-ai`  
✅ **AI node**: System message + user prompt  
✅ **Response node**: Any format above  
✅ **Test**: Run test scripts  
✅ **Activate**: Toggle workflow to "Active"  

Your AI integration will work perfectly! 🎉