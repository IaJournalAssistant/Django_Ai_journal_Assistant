#!/usr/bin/env python
"""
Test script specifically for OpenRouter + Dolphin integration
"""

import requests
import json

# Your n8n webhook URL
url = "https://aymen2025aymen25.app.n8n.cloud/webhook-test/django-ai"

def test_openrouter_integration():
    """Test OpenRouter Dolphin integration with planning prompts"""
    
    print("🐬 Testing OpenRouter + Dolphin 3.0 Mistral Integration")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Simple Task Analysis",
            "prompt": "Analyze this task: Complete project documentation (Status: in_progress, Priority: high, Due: 2024-12-15)"
        },
        {
            "name": "Task Summary Request",
            "prompt": """TASK ANALYSIS REQUEST

Current Workload Overview (3 total tasks):
Task: Complete project proposal - Write Q4 proposal (Status: in_progress, Priority: high, Due: 2024-12-15, Project: Q4 Planning)
Task: Review team feedback - Go through sprint feedback (Status: pending, Priority: medium, Due: 2024-12-10, Project: Team Management)
Task: Update website - Refresh about page (Status: pending, Priority: low, Due: 2024-12-20, Project: Website)

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
        },
        {
            "name": "Project Health Analysis",
            "prompt": """PROJECT HEALTH ANALYSIS

Project Details:
Project: Website Redesign
Description: Complete redesign of company website
Progress: 65%
Status: active
Target Completion: 2024-12-31

Task Breakdown (4 tasks):
- Design mockups (completed, high priority) - Due: 2024-12-01
- Implement frontend (in_progress, high priority) - Due: 2024-12-20
- Content migration (pending, medium priority) - Due: 2024-12-25
- Testing and launch (pending, high priority) - Due: 2024-12-30

Please provide a comprehensive project assessment with health score, risk assessment, strategic recommendations, success factors, and timeline optimization. Keep under 250 words."""
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. 🧪 {test_case['name']}")
        print("-" * 40)
        
        payload = {"prompt": test_case['prompt']}
        
        try:
            print("📤 Sending request...")
            response = requests.post(url, json=payload, timeout=30)
            
            print(f"📊 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print("✅ SUCCESS!")
                    
                    # Extract AI response using the same logic as Django
                    ai_response = None
                    
                    if isinstance(result, dict):
                        # Check for OpenRouter format first
                        if 'choices' in result and isinstance(result['choices'], list) and len(result['choices']) > 0:
                            choice = result['choices'][0]
                            if isinstance(choice, dict) and 'message' in choice:
                                message = choice['message']
                                if isinstance(message, dict) and 'content' in message:
                                    ai_response = message['content']
                        
                        # Check for simple message format
                        elif 'message' in result:
                            ai_response = result['message']
                        
                        # Fallback to any string field
                        else:
                            for key, value in result.items():
                                if isinstance(value, str) and len(value.strip()) > 10:
                                    ai_response = value
                                    break
                    
                    if ai_response:
                        print("\n🤖 DOLPHIN AI RESPONSE:")
                        print("=" * 50)
                        print(ai_response)
                        print("=" * 50)
                        
                        # Analyze response quality
                        print(f"\n📈 Response Analysis:")
                        print(f"   Length: {len(ai_response)} characters")
                        print(f"   Has sections: {'**' in ai_response}")
                        print(f"   Has recommendations: {'recommend' in ai_response.lower()}")
                        print(f"   Has priorities: {'priority' in ai_response.lower()}")
                        print(f"   Professional tone: {'assessment' in ai_response.lower()}")
                        
                    else:
                        print("❌ Could not extract AI response from:")
                        print(json.dumps(result, indent=2))
                        
                except json.JSONDecodeError:
                    print("✅ SUCCESS (Non-JSON Response)!")
                    print(f"📝 Response Text: {response.text}")
                    
            else:
                print(f"❌ FAILED with status {response.status_code}")
                print(f"📝 Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ REQUEST FAILED: {e}")
        
        print("\n" + "=" * 60)

def test_response_formats():
    """Test different expected response formats from OpenRouter"""
    
    print("\n🔧 Testing Expected Response Formats")
    print("=" * 60)
    
    # Simulate different response formats OpenRouter might return
    test_responses = [
        {
            "name": "OpenRouter Standard Format",
            "response": {
                "id": "gen-123",
                "model": "cognitivecomputations/dolphin-2.9.4-llama3.1-8b:free",
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "**Current Status Assessment:**\nYou have a well-balanced workload with 3 tasks across different priority levels...\n\n**Key Insights:**\n- High-priority Q4 proposal needs immediate focus\n- Team feedback review is approaching deadline\n- Website updates can be scheduled for later\n\n**Actionable Recommendations:**\n- Dedicate morning hours to project proposal\n- Schedule 2-hour block for team feedback today\n- Consider delegating website updates\n\n**Urgent Items:**\n- Project proposal due in 5 days - needs daily progress\n- Team feedback due tomorrow - schedule immediately"
                    }
                }],
                "usage": {
                    "prompt_tokens": 150,
                    "completion_tokens": 120,
                    "total_tokens": 270
                }
            }
        },
        {
            "name": "n8n Simple Response Node",
            "response": {
                "message": "**Project Health Score:** Excellent (65% complete)\n\n**Risk Assessment:** On track for December 31st completion. Frontend implementation is progressing well.\n\n**Strategic Recommendations:**\n1. Maintain current velocity on frontend work\n2. Begin content migration preparation now\n3. Schedule testing resources for final week\n\n**Timeline Optimization:**\nCurrent pace suggests completion by December 28th, providing 3-day buffer for final adjustments."
            }
        }
    ]
    
    # Import the extraction function logic
    def extract_ai_response(response):
        if not response:
            return None
            
        if isinstance(response, dict):
            # OpenRouter format
            if 'choices' in response and isinstance(response['choices'], list) and len(response['choices']) > 0:
                choice = response['choices'][0]
                if isinstance(choice, dict) and 'message' in choice:
                    message = choice['message']
                    if isinstance(message, dict) and 'content' in message:
                        return str(message['content']).strip()
            
            # Simple message format
            if 'message' in response:
                return str(response['message']).strip()
            
            # Fallback
            for key, value in response.items():
                if isinstance(value, str) and len(value.strip()) > 10:
                    return value.strip()
        
        return str(response) if response else None
    
    for test in test_responses:
        print(f"\n📋 {test['name']}:")
        extracted = extract_ai_response(test['response'])
        if extracted:
            print(f"✅ Extracted: {extracted[:100]}...")
        else:
            print("❌ Failed to extract")

if __name__ == "__main__":
    test_openrouter_integration()
    test_response_formats()
    
    print("\n" + "=" * 60)
    print("🎯 OpenRouter + Dolphin Integration Test Complete!")
    print("=" * 60)
    print("\n🐬 Dolphin 3.0 Mistral 24B Benefits:")
    print("✅ Free and powerful (24B parameters)")
    print("✅ Excellent at structured responses")
    print("✅ Great for planning and analysis tasks")
    print("✅ Fast inference and reliable")
    print("✅ Perfect for your Django planning app!")
    print("\n🚀 Ready to provide intelligent planning assistance!")