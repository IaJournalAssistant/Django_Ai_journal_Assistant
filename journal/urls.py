from django.urls import path
from .views import JournalEntryViewSet, journal_list, journal_create, journal_detail

# Remove router registration since we'll use direct paths
urlpatterns = [
    # Template views
    path('', journal_list, name='journal-list'),
    path('create/', journal_create, name='journal-create'),
    path('<int:pk>/', journal_detail, name='journal-detail'),
    # API endpoints mapped to same URLs
    path('', JournalEntryViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('<int:pk>/', JournalEntryViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    })),
]