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
    
    def send_journal_created(self, journal_entry) -> dict:
        """
        Send journal creation data to n8n webhook and get AI response
        
        Args:
            journal_entry: JournalEntry instance
            
        Returns:
            dict: Response with success status and AI summary
        """
        try:
            # Prepare payload for your n8n workflow
            payload = {
                "event": "journal_created",
                "journal": {
                    "id": journal_entry.id,
                    "title": journal_entry.title,
                    "content": journal_entry.content,
                    "author": journal_entry.author.username,
                    "created_at": journal_entry.created_at.isoformat(),
                },
                "timestamp": journal_entry.created_at.isoformat()
            }
            
            logger.info(f"Sending journal {journal_entry.id} to n8n webhook")
            logger.info(f"Payload: {payload}")
            
            # Send POST request to n8n webhook and wait for response
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=30,  # Increased timeout for AI processing
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Django-Journal-App'
                }
            )
            
            # Check if request was successful
            response.raise_for_status()
            
            logger.info(f"n8n webhook response status: {response.status_code}")
            logger.info(f"n8n webhook response text: {response.text}")
            
            # Simple response parsing - just use whatever n8n returns
            ai_summary = response.text.strip()
            logger.info(f"AI response: {ai_summary}")
            
            return {
                "success": True,
                "ai_summary": ai_summary,
                "status_code": response.status_code,
                "journal_id": journal_entry.id
            }
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout waiting for AI response for journal {journal_entry.id}: {str(e)}")
            return {"success": False, "error": "AI processing timeout"}
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 404:
                logger.error(f"n8n webhook not found (404) - workflow may not be active")
                return {"success": False, "error": "Webhook not found - check if n8n workflow is active"}
            logger.error(f"HTTP error sending journal {journal_entry.id}: {str(e)}")
            return {"success": False, "error": str(e)}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send journal {journal_entry.id} to n8n webhook: {str(e)}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error sending journal {journal_entry.id} to n8n webhook: {str(e)}")
            return {"success": False, "error": str(e)}
    

    



# Global instance
webhook_service = N8nWebhookService()