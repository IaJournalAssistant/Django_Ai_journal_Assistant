from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from rest_framework import viewsets, permissions
from .serializers import JournalEntrySerializer
from .models import JournalEntry, Note, Tag
from .nlp_utils import predict_tags_for_texts
import logging
from .forms import JournalEntryForm, NoteForm, TagForm
from media_manager.models import MediaFile

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
        form = JournalEntryForm(request.POST)
        if form.is_valid():
            journal = form.save(commit=False)
            journal.author = request.user
            journal.save()
            
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
        form = JournalEntryForm()
    
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


# ----------------------
# Notes CRUD views
# ----------------------


@login_required
def note_list(request):
    q = request.GET.get('q', '').strip()
    notes = Note.objects.filter(author=request.user)
    if q:
        # search in title, content, or tag name
        notes = notes.filter(
            Q(title__icontains=q) | Q(content__icontains=q) | Q(tags__name__icontains=q)
        )
    # Materialize the queryset so we can attach a transient `predicted_tag`
    # attribute to notes that do not yet have one. This keeps DB access
    # minimal and allows batch NLP processing.
    notes = list(notes.order_by('-updated_at'))

    # Attach predicted_tag for notes without assigned tags. We fetch all
    # Tag objects once and run batched prediction (spaCy pipe or fallback).
    try:
        tags_all = list(Tag.objects.all())
        if tags_all:
            # notes.tags is a ForeignKey on this project (single tag per note).
            # For ForeignKey use a simple None check to detect notes without tags.
            notes_without_tags = [n for n in notes if n.tags is None]
            if notes_without_tags:
                # Safety limit to avoid processing extremely large sets in one go.
                MAX_PREDICT = 500
                to_predict = notes_without_tags[:MAX_PREDICT]
                contents = [getattr(n, 'content', '') or getattr(n, 'title', '') or '' for n in to_predict]
                predicted_names = predict_tags_for_texts(contents, tags_all)
                name_map = {t.name.lower(): t for t in tags_all}
                for note_obj, pred_name in zip(to_predict, predicted_names):
                    note_obj.predicted_tag = name_map.get(pred_name.lower()) if pred_name else None
                # For notes beyond the safety limit, set predicted_tag to None
                for n in notes_without_tags[MAX_PREDICT:]:
                    n.predicted_tag = None
        # Ensure every note has the attribute (templates may expect it)
        for n in notes:
            if not hasattr(n, 'predicted_tag'):
                n.predicted_tag = None
    except Exception as e:
        logging.getLogger(__name__).exception('Tag prediction failed: %s', e)
        for n in notes:
            if not hasattr(n, 'predicted_tag'):
                n.predicted_tag = None

    return render(request, 'journal/notes_list.html', {'notes': notes, 'q': q})


@login_required
def note_create(request):
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.author = request.user
            note.save()
            # tags are a ForeignKey (single selection) so no m2m handling needed
            # After creating a note, take the user to the notes list per user request
            return redirect('note-list')
    else:
        form = NoteForm()
    return render(request, 'journal/note_form.html', {'form': form})


@login_required
def note_detail(request, pk):
    note = get_object_or_404(Note, pk=pk, author=request.user)

    if request.method == 'POST':
        if 'update_note' in request.POST:
            form = NoteForm(request.POST, instance=note)
            if form.is_valid():
                form.save()
                # After update, redirect back to the notes list for consistency
                return redirect('note-list')
            # If form invalid, render the detail page with errors so user can fix
            return render(request, 'journal/note_detail.html', {'note': note, 'form': form})

        elif 'delete_note' in request.POST:
            note.delete()
            return redirect('note-list')

    form = NoteForm(instance=note)
    return render(request, 'journal/note_detail.html', {'note': note, 'form': form})


# ----------------------
# Tag management views
# ----------------------


@login_required
def tag_list(request):
    tags = Tag.objects.all()
    return render(request, 'journal/tags_list.html', {'tags': tags})


@login_required
def tag_create(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save()
            return redirect('tag-list')
    else:
        form = TagForm()
    return render(request, 'journal/tag_form.html', {'form': form})


@login_required
def tag_edit(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            return redirect('tag-list')
    else:
        form = TagForm(instance=tag)
    return render(request, 'journal/tag_form.html', {'form': form, 'tag': tag})


@login_required
def tag_delete(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    if request.method == 'POST':
        tag.delete()
        return redirect('tag-list')
    return render(request, 'journal/tag_confirm_delete.html', {'tag': tag})

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
