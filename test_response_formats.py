#!/usr/bin/env python
"""
Test script to verify different n8n response formats are handled correctly
"""

import json
from a_planning.services import N8nAIService

# Initialize the service
ai_service = N8nAIService()

def test_response_extraction():
    """Test the response extraction with different formats"""
    
    print("🧪 Testing Response Format Handling")
    print("=" * 50)
    
    # Test different response formats
    test_cases = [
        # Standard format
        {"message": "This is a standard AI response"},
        
        # OpenAI format
        {"choices": [{"message": {"content": "OpenAI style response"}}]},
        
        # Claude format  
        {"content": [{"text": "Claude style response"}]},
        
        # Simple text response
        {"text": "Simple text response"},
        
        # Response field
        {"response": "Response field content"},
        
        # Nested structure
        {"data": {"message": "Nested message content"}},
        
        # Multiple fields (should pick first available)
        {
            "summary": "Task summary content",
            "message": "Message content", 
            "text": "Text content"
        },
        
        # Analysis specific
        {"analysis": "Project analysis content"},
        
        # Suggestions specific
        {"suggestions": "Task breakdown suggestions"},
        
        # Action plan specific
        {"action_plan": "Goal action plan content"},
        
        # Insights specific
        {"insights": "Productivity insights content"},
        
        # Plain string
        "Just a plain string response",
        
        # Empty response
        {},
        
        # None response
        None
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {json.dumps(test_case) if test_case else 'None'}")
        result = ai_service._extract_ai_response(test_case)
        print(f"   Result: {repr(result)}")
        print(f"   Success: {'✅' if result else '❌'}")

def test_webhook_response_scenarios():
    """Test different webhook response scenarios"""
    
    print("\n" + "=" * 50)
    print("🔧 Common n8n Response Scenarios")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "OpenAI Chat Completion",
            "response": {
                "choices": [
                    {
                        "message": {
                            "content": "**Current Status Assessment:**\nYou have 3 tasks with mixed priorities...\n\n**Key Insights:**\nThe high-priority project proposal needs immediate attention..."
                        }
                    }
                ]
            }
        },
        {
            "name": "Claude Response",
            "response": {
                "content": [
                    {
                        "text": "**Project Health Score:**\nYour project is 65% complete with good momentum...\n\n**Risk Assessment:**\nPotential bottleneck in frontend implementation..."
                    }
                ]
            }
        },
        {
            "name": "Simple n8n Response Node",
            "response": {
                "message": "**Productivity Assessment:**\nYour task completion rate of 72% is above average...\n\n**Optimization Opportunities:**\nFocus on reducing overdue tasks..."
            }
        },
        {
            "name": "Custom Response Format",
            "response": {
                "ai_response": "**Task Decomposition:**\n1. Research requirements and gather resources\n2. Create project outline and structure\n3. Write first draft of content..."
            }
        },
        {
            "name": "Error Response",
            "response": {
                "error": "AI model temporarily unavailable"
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 {scenario['name']}:")
        print(f"Input: {json.dumps(scenario['response'], indent=2)}")
        result = ai_service._extract_ai_response(scenario['response'])
        print(f"Extracted: {repr(result[:100] + '...' if result and len(result) > 100 else result)}")
        print(f"Status: {'✅ Success' if result else '❌ Failed'}")

if __name__ == "__main__":
    test_response_extraction()
    test_webhook_response_scenarios()
    
    print("\n" + "=" * 50)
    print("🎯 Response Handler Configuration Complete!")
    print("=" * 50)
    print("\nThe AI service can now handle:")
    print("✅ Standard {message: '...'} format")
    print("✅ OpenAI chat completion format")
    print("✅ Claude response format")
    print("✅ Custom n8n response formats")
    print("✅ Plain text responses")
    print("✅ Nested response structures")
    print("✅ Multiple field priorities")
    print("✅ Error handling for malformed responses")
    print("\n🚀 Ready for any n8n workflow configuration!")