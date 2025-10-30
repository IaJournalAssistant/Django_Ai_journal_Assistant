"""
Webhook service for sending journal data to n8n
"""

import requests
import logging
from django.conf import settings
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class N8nWebhookService:
    """Service for sending data to n8n webhooks"""
    
    def __init__(self):
        # n8n webhook URL - you can move this to settings.py later
        self.webhook_url = "http://192.168.1.42:5678/webhook-test/34139a30-bd34-4983-a56a-f57f4ca3e771"
        self.timeout = 10  # seconds
    
    def send_journal_created(self, journal_entry) -> bool:
        """
        Send journal creation data to n8n webhook
        
        Args:
            journal_entry: JournalEntry instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Prepare payload
            payload = {
                "event": "journal_created",
                "journal": {
                    "id": journal_entry.id,
                    "title": journal_entry.title,
                    "content": journal_entry.content,
                    "author": journal_entry.author.username,
                    "created_at": journal_entry.created_at.isoformat(),
                },
                "timestamp": journal_entry.created_at.isoformat(),
                # Add response webhook URL for n8n to send data back
                "response_webhook": f"http://127.0.0.1:8000/journal/ai-response/"
            }
            
            logger.info(f"Sending journal {journal_entry.id} to n8n webhook")
            
            # Send POST request to n8n webhook
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Django-Journal-App'
                }
            )
            
            # Check if request was successful
            response.raise_for_status()
            
            logger.info(f"Successfully sent journal {journal_entry.id} to n8n webhook. Status: {response.status_code}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send journal {journal_entry.id} to n8n webhook: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending journal {journal_entry.id} to n8n webhook: {str(e)}")
            return False
    
    def test_webhook(self) -> Dict[str, Any]:
        """
        Test the webhook connection with detailed debugging
        
        Returns:
            dict: Test result with status and message
        """
        try:
            test_payload = {
                "event": "test",
                "message": "Testing webhook connection from Django",
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            logger.info(f"Testing webhook URL: {self.webhook_url}")
            logger.info(f"Test payload: {test_payload}")
            
            response = requests.post(
                self.webhook_url,
                json=test_payload,
                timeout=self.timeout,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Django-Journal-App-Test'
                }
            )
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            logger.info(f"Response text: {response.text}")
            
            response.raise_for_status()
            
            return {
                "success": True,
                "status_code": response.status_code,
                "message": "Webhook test successful",
                "response_text": response.text[:200],  # First 200 chars
                "response_headers": dict(response.headers)
            }
            
        except requests.exceptions.ConnectionError as e:
            return {
                "success": False,
                "error": f"Connection Error: {str(e)}",
                "message": "Cannot connect to n8n server. Check if n8n is running.",
                "troubleshooting": [
                    "1. Check if n8n server is running at 192.168.1.42:5678",
                    "2. Try accessing http://192.168.1.42:5678 in your browser",
                    "3. Check network connectivity between Django and n8n server"
                ]
            }
        except requests.exceptions.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP Error: {str(e)}",
                "message": "n8n server responded with an error",
                "status_code": e.response.status_code if e.response else None,
                "response_text": e.response.text if e.response else None,
                "troubleshooting": [
                    "1. Check if the webhook URL is correct",
                    "2. Ensure the n8n workflow is active",
                    "3. Verify the webhook node is properly configured"
                ]
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Webhook test failed"
            }
    
    def test_n8n_server(self) -> Dict[str, Any]:
        """
        Test if n8n server is reachable
        
        Returns:
            dict: Server connectivity test result
        """
        try:
            # Test basic connectivity to n8n server
            base_url = "http://192.168.1.42:5678"
            
            response = requests.get(
                base_url,
                timeout=5,
                headers={'User-Agent': 'Django-Journal-App-Test'}
            )
            
            return {
                "success": True,
                "status_code": response.status_code,
                "message": "n8n server is reachable",
                "server_response": response.text[:100]
            }
            
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": "Cannot connect to n8n server",
                "troubleshooting": [
                    "1. Check if n8n is running: docker ps (if using Docker)",
                    "2. Check if port 5678 is open on the VM",
                    "3. Try: curl http://192.168.1.42:5678",
                    "4. Check VM firewall settings"
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Server connectivity test failed"
            }


# Global instance
webhook_service = N8nWebhookService()