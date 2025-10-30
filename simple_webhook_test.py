#!/usr/bin/env python
"""
Simple test for n8n webhook - run this after clicking 'Execute workflow' in n8n
"""

import requests

url = "https://aymen2025aymen25.app.n8n.cloud/webhook-test/django-ai"
payload = {"prompt": "Write a short summary about task management"}

print("🧪 Simple n8n Webhook Test")
print("=" * 40)
print(f"URL: {url}")
print(f"Payload: {payload}")
print("=" * 40)

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS!")
        print(f"Response: {response.text}")
    else:
        print(f"❌ FAILED: {response.text}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n💡 Remember to:")
print("1. Click 'Execute workflow' in n8n first")
print("2. Make sure your workflow is active")
print("3. Check that the webhook path matches: /webhook-test/django-ai")