from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from rest_framework import viewsets, permissions
from .serializers import JournalEntrySerializer
from .models import JournalEntry
from .forms import JournalEntryForm, UnifiedNoteForm
from media_manager.models import MediaFile
import re

# ✅ REST API viewset (if you ever use API routes)
class JournalEntryViewSet(viewsets.ModelViewSet):
    serializer_class = JournalEntrySerializer  # 🔹 fixed typo: was "sserlizer_class"
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return JournalEntry.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


# ✅ HTML view for listing all journal entries
@login_required
def journal_list(request):
    entries = JournalEntry.objects.filter(author=request.user).order_by('-created_at')
    return render(request, 'journal/list.html', {'entries': entries})


# ✅ HTML view for creating a journal entry via form with media upload
@login_required
def journal_create(request):
    if request.method == 'POST':
        content = request.POST.get('content', '')
        title = request.POST.get('title', '') or extract_title_from_content(content)
        
        # Create journal entry
        journal = JournalEntry.objects.create(
            author=request.user,
            title=title,
            content=content
        )
        
        # Handle multiple file uploads
        files = request.FILES.getlist('files')
        for file in files:
            if file:
                # Auto-detect file type
                file_type = detect_file_type(file.name)
                caption = request.POST.get(f'caption_{file.name}', '')
                
                MediaFile.objects.create(
                    uploaded_by=request.user,
                    journal=journal,
                    file=file,
                    file_type=file_type,
                    caption=caption
                )
        
        # Handle voice recordings
        voice_recordings = request.FILES.getlist('voice_recordings')
        for i, voice_file in enumerate(voice_recordings):
            if voice_file:
                caption = request.POST.get(f'voice_caption_{i}', '')
                
                MediaFile.objects.create(
                    uploaded_by=request.user,
                    journal=journal,
                    file=voice_file,
                    file_type='audio',
                    caption=caption or 'Voice Recording'
                )
        
        return redirect('journal-detail', pk=journal.id)
    else:
        form = UnifiedNoteForm()
    
    return render(request, 'journal/create.html', {'form': form})

@login_required
def journal_detail(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, author=request.user)
    media_files = entry.media_files.all().order_by('-uploaded_at')
    
    if request.method == 'POST':
        # Handle journal update
        if 'update_journal' in request.POST:
            form = JournalEntryForm(request.POST, instance=entry)
            if form.is_valid():
                form.save()
                return JsonResponse({'success': True})
            return JsonResponse({'success': False, 'errors': form.errors})
        
        # Handle new media upload
        elif 'upload_media' in request.POST:
            files = request.FILES.getlist('files')
            uploaded_files = []
            
            for file in files:
                if file:
                    file_type = detect_file_type(file.name)
                    caption = request.POST.get(f'caption_{file.name}', '')
                    
                    media_file = MediaFile.objects.create(
                        uploaded_by=request.user,
                        journal=entry,
                        file=file,
                        file_type=file_type,
                        caption=caption
                    )
                    uploaded_files.append({
                        'id': media_file.id,
                        'name': media_file.file.name,
                        'type': media_file.file_type,
                        'url': media_file.file.url,
                        'caption': media_file.caption
                    })
            
            # Handle voice recordings
            voice_recordings = request.FILES.getlist('voice_recordings')
            for i, voice_file in enumerate(voice_recordings):
                if voice_file:
                    caption = request.POST.get(f'voice_caption_{i}', '')
                    
                    media_file = MediaFile.objects.create(
                        uploaded_by=request.user,
                        journal=entry,
                        file=voice_file,
                        file_type='audio',
                        caption=caption or 'Voice Recording'
                    )
                    uploaded_files.append({
                        'id': media_file.id,
                        'name': media_file.file.name,
                        'type': media_file.file_type,
                        'url': media_file.file.url,
                        'caption': media_file.caption
                    })
            
            return JsonResponse({'success': True, 'files': uploaded_files})
    
    form = JournalEntryForm(instance=entry)
    return render(request, 'journal/journalDetails.html', {
        'entry': entry,
        'form': form,
        'media_files': media_files
    })

def extract_title_from_content(content):
    """Extract title from markdown-style content"""
    if not content:
        return 'Untitled Note'
    
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        # Check for markdown heading
        if line.startswith('# '):
            return line[2:].strip()
        # Check for first non-empty line that's not markdown syntax
        elif line and not line.startswith('#') and not line.startswith('-') and not line.startswith('*') and not line.startswith('['):
            # Take first 50 characters as title
            return line[:50].strip()
    
    return 'Untitled Note'

def detect_file_type(filename):
    """Auto-detect file type based on extension"""
    filename = filename.lower()
    
    image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp']
    video_exts = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']
    audio_exts = ['.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac', '.wma']
    doc_exts = ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt']
    
    if any(filename.endswith(ext) for ext in image_exts):
        return 'image'
    elif any(filename.endswith(ext) for ext in video_exts):
        return 'video'
    elif any(filename.endswith(ext) for ext in audio_exts):
        return 'audio'
    elif any(filename.endswith(ext) for ext in doc_exts):
        return 'document'
    else:
        return 'other'
