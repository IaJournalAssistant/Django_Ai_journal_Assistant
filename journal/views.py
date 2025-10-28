from django.shortcuts import render, redirect
from rest_framework import viewsets, permissions
from .serializers import JournalEntrySerializer
from .models import JournalEntry

# ✅ REST API viewset (if you ever use API routes)
class JournalEntryViewSet(viewsets.ModelViewSet):
    serializer_class = JournalEntrySerializer  # 🔹 fixed typo: was "sserlizer_class"
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JournalEntry.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


# ✅ HTML view for listing all journal entries
def journal_list(request):
    entries = JournalEntry.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'journal/list.html', {'entries': entries})


# ✅ HTML view for creating a journal entry via form
def journal_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')

        if title and content:  # optional validation
            JournalEntry.objects.create(author=request.user, title=title, content=content)
            return redirect('journal-list')

        # If missing data, re-render the form with an error
        return render(request, 'journal/create.html', {'error': 'Title and content are required.'})

    return render(request, 'journal/create.html')
