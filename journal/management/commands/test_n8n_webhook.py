"""
Django management command to test n8n webhook connection
Usage: python manage.py test_n8n_webhook
"""

from django.core.management.base import BaseCommand
from journal.webhook_service import webhook_service


class Command(BaseCommand):
    help = 'Test n8n webhook connection with detailed debugging'

    def add_arguments(self, parser):
        parser.add_argument(
            '--server-only',
            action='store_true',
            help='Test only server connectivity, not webhook',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('=== n8n Webhook Debugging ==='))
        self.stdout.write(f'Webhook URL: {webhook_service.webhook_url}')
        
        # Step 1: Test server connectivity
        self.stdout.write('\n1. Testing n8n server connectivity...')
        server_result = webhook_service.test_n8n_server()
        
        if server_result['success']:
            self.stdout.write(
                self.style.SUCCESS(f'✓ n8n server is reachable!')
            )
            self.stdout.write(f'Status Code: {server_result["status_code"]}')
        else:
            self.stdout.write(
                self.style.ERROR(f'✗ Cannot reach n8n server!')
            )
            self.stdout.write(f'Error: {server_result["message"]}')
            
            if 'troubleshooting' in server_result:
                self.stdout.write('\nTroubleshooting steps:')
                for step in server_result['troubleshooting']:
                    self.stdout.write(f'  {step}')
            
            return  # Exit if server is not reachable
        
        if options['server_only']:
            return
        
        # Step 2: Test webhook
        self.stdout.write('\n2. Testing webhook endpoint...')
        webhook_result = webhook_service.test_webhook()
        
        if webhook_result['success']:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Webhook test successful!')
            )
            self.stdout.write(f'Status Code: {webhook_result["status_code"]}')
            self.stdout.write(f'Response: {webhook_result["response_text"]}')
        else:
            self.stdout.write(
                self.style.ERROR(f'✗ Webhook test failed!')
            )
            self.stdout.write(f'Error: {webhook_result["error"]}')
            
            if 'troubleshooting' in webhook_result:
                self.stdout.write('\nTroubleshooting steps:')
                for step in webhook_result['troubleshooting']:
                    self.stdout.write(f'  {step}')
        
        # Step 3: n8n Configuration Guide
        self.stdout.write('\n' + self.style.HTTP_INFO('=== n8n Configuration Guide ==='))
        self.stdout.write('If webhook failed, follow these steps in n8n:')
        self.stdout.write('')
        self.stdout.write('1. CREATE NEW WORKFLOW:')
        self.stdout.write('   - Go to http://192.168.1.42:5678')
        self.stdout.write('   - Click "New Workflow"')
        self.stdout.write('')
        self.stdout.write('2. ADD WEBHOOK NODE:')
        self.stdout.write('   - Add "Webhook" node')
        self.stdout.write('   - Set HTTP Method: POST')
        self.stdout.write('   - Set Path: webhook-test/34139a30-bd34-4983-a56a-f57f4ca3e771')
        self.stdout.write('   - Authentication: None')
        self.stdout.write('')
        self.stdout.write('3. ADD DEBUG NODE (optional):')
        self.stdout.write('   - Add "Set" or "Code" node after webhook')
        self.stdout.write('   - This will help you see the received data')
        self.stdout.write('')
        self.stdout.write('4. ACTIVATE WORKFLOW:')
        self.stdout.write('   - Click "Active" toggle (should be ON)')
        self.stdout.write('   - Save the workflow')
        self.stdout.write('')
        self.stdout.write('5. TEST AGAIN:')
        self.stdout.write('   - Run: python manage.py test_n8n_webhook')
        self.stdout.write('')
        self.stdout.write('Expected webhook payload:')
        self.stdout.write('''{
  "event": "journal_created",
  "journal": {
    "id": 123,
    "title": "Journal Title",
    "content": "Journal content...",
    "author": "username",
    "created_at": "2024-01-01T12:00:00Z"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}''')