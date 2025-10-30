from django.urls import path
from .views import (
    JournalEntryViewSet,
    journal_list,
    journal_create,
    journal_detail,
    note_list,
    note_create,
    note_detail,
    tag_list,
    tag_create,
    tag_edit,
    tag_delete,
    receive_ai_response,
    get_ai_response,
    delete_journal

)

urlpatterns = [
    # Journal template views
    path('', journal_list, name='journal-list'),
    path('create/', journal_create, name='journal-create'),
    path('<int:pk>/', journal_detail, name='journal-detail'),

    # Notes CRUD
    path('notes/', note_list, name='note-list'),
    path('notes/create/', note_create, name='note-create'),
    path('notes/<int:pk>/', note_detail, name='note-detail'),

    # Tags CRUD
    path('tags/', tag_list, name='tag-list'),
    path('tags/create/', tag_create, name='tag-create'),
    path('tags/<slug:slug>/edit/', tag_edit, name='tag-edit'),
    path('tags/<slug:slug>/delete/', tag_delete, name='tag-delete'),

    # API endpoints (ViewSet)
    path('api/', JournalEntryViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-journal-list'),
    path('api/<int:pk>/', JournalEntryViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='api-journal-detail'),

    # Delete journal (function-based)
    path('<int:pk>/delete/', delete_journal, name='journal-delete'),

    # AI response endpoints
    path('ai-response/', receive_ai_response, name='receive-ai-response'),  # For n8n to send data
    path('ai-response/<int:journal_id>/', get_ai_response, name='get-ai-response'),  # For frontend to check
]
