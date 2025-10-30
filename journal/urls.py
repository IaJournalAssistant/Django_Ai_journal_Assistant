from django.urls import path
from .views import (
    JournalEntryViewSet, journal_list, journal_create, journal_detail, 
    receive_ai_response, get_ai_response, delete_journal
)

# Remove router registration since we'll use direct paths
urlpatterns = [
    # Template views
    path('', journal_list, name='journal-list'),
    path('create/', journal_create, name='journal-create'),
    path('<int:pk>/', journal_detail, name='journal-detail'),
    path('<int:pk>/delete/', delete_journal, name='journal-delete'),
    
    # AI response endpoints
    path('ai-response/', receive_ai_response, name='receive-ai-response'),  # For n8n to send data
    path('ai-response/<int:journal_id>/', get_ai_response, name='get-ai-response'),  # For frontend to check
    
    # API endpoints mapped to same URLs
    path('', JournalEntryViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('<int:pk>/', JournalEntryViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    })),
]
