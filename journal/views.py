from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from django.db.models import Q
from .models import JournalEntry, Note, Tag
from .nlp_utils import predict_tags_for_texts, extract_potential_tag_from_text
import logging
from .forms import JournalEntryForm, NoteForm, TagForm
from django.utils import timezone
from rest_framework import viewsets, permissions
from .serializers import JournalEntrySerializer
from .forms import UnifiedNoteForm

from media_manager.models import MediaFile
from .webhook_service import webhook_service
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
        
        # Send to n8n webhook and get AI response
        try:
            ai_response = webhook_service.send_journal_created(journal)
            if ai_response and ai_response.get('success'):
                # Store AI response in cache immediately
                from django.core.cache import cache
                cache_key = f"ai_response_{journal.id}"
                ai_data = {
                    'response': ai_response.get('ai_summary', ''),
                    'type': 'analysis',
                    'timestamp': timezone.now().isoformat(),
                    'received_at': timezone.now().isoformat()
                }
                cache.set(cache_key, ai_data, timeout=3600)
        except Exception as e:
            # Log error but don't fail the journal creation
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to send journal {journal.id} to webhook: {str(e)}")
        
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
                
                media_file = MediaFile.objects.create(
                    uploaded_by=request.user,
                    journal=journal,
                    file=voice_file,
                    file_type='audio',
                    caption=caption or 'Voice Recording'
                )
                
                # Trigger transcription manually if signals don't work
                try:
                    from media_manager.speech_to_text import process_audio_transcription
                    import threading
                    
                    # Process transcription in background thread to avoid blocking
                    def transcribe_async():
                        process_audio_transcription(media_file.id)
                    
                    thread = threading.Thread(target=transcribe_async)
                    thread.daemon = True
                    thread.start()
                    
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Failed to start transcription for media file {media_file.id}: {str(e)}")
        
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
        notes_without_tags = [n for n in notes if n.tags is None]
        
        if notes_without_tags:
            # Safety limit to avoid processing extremely large sets in one go.
            MAX_PREDICT = 500
            to_predict = notes_without_tags[:MAX_PREDICT]
            
            # Combine title and content for better AI analysis
            # This gives the AI more context to make accurate predictions
            combined_texts = []
            for n in to_predict:
                title = getattr(n, 'title', '') or ''
                content = getattr(n, 'content', '') or ''
                # Combine title and content with title given more weight
                combined = f"{title}. {content}" if title and content else (title or content)
                combined_texts.append(combined)
            
            # Try to predict from existing tags first with higher confidence threshold
            # min_confidence=0.5 means we need strong similarity to use existing tags
            predicted_names = predict_tags_for_texts(combined_texts, tags_all, min_confidence=0.5) if tags_all else [None] * len(combined_texts)
            name_map = {t.name.lower(): t for t in tags_all}
            
            # Process predictions and create new tags if needed
            for note_obj, pred_name, combined_text in zip(to_predict, predicted_names, combined_texts):
                if pred_name:
                    # Found a match in existing tags
                    note_obj.predicted_tag = name_map.get(pred_name.lower())
                else:
                    # No good match found - try to create a new tag from content
                    new_tag_name = extract_potential_tag_from_text(combined_text)
                    
                    if new_tag_name:
                        # Check if this tag name already exists (case-insensitive)
                        existing_tag = Tag.objects.filter(name__iexact=new_tag_name).first()
                        
                        if existing_tag:
                            note_obj.predicted_tag = existing_tag
                        else:
                            # Create new tag automatically
                            try:
                                new_tag = Tag.objects.create(name=new_tag_name)
                                note_obj.predicted_tag = new_tag
                                # Add to tags_all and name_map for subsequent notes
                                tags_all.append(new_tag)
                                name_map[new_tag.name.lower()] = new_tag
                                logger = logging.getLogger(__name__)
                                logger.info(f"AI auto-created new tag: '{new_tag_name}'")
                            except Exception as create_error:
                                logger = logging.getLogger(__name__)
                                logger.warning(f"Failed to create new tag '{new_tag_name}': {str(create_error)}")
                                note_obj.predicted_tag = None
                    else:
                        note_obj.predicted_tag = None
            
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
 



from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@csrf_exempt
@require_http_methods(["POST"])
def receive_ai_response(request):
    """
    Receive AI response from n8n webhook
    This endpoint will be called by n8n after AI processing
    """
    try:
        # Parse the incoming JSON data
        data = json.loads(request.body)
        
        # Extract journal ID and AI response
        journal_id = data.get('journal_id')
        ai_response = data.get('ai_response', '')
        response_type = data.get('response_type', 'analysis')  # analysis, summary, etc.
        
        if not journal_id:
            return JsonResponse({'error': 'journal_id is required'}, status=400)
        
        # Get the journal entry
        try:
            journal = JournalEntry.objects.get(id=journal_id)
        except JournalEntry.DoesNotExist:
            return JsonResponse({'error': 'Journal not found'}, status=404)
        
        # Store the AI response (you can extend JournalEntry model or create a separate model)
        # For now, we'll use a simple approach with session storage
        
        # Log the complete request for debugging
        import logging
        logger = logging.getLogger(__name__)
        
        # Log what n8n actually sent
        logger.info(f"=== n8n Webhook Received ===")
        logger.info(f"Raw request body: {request.body.decode()}")
        logger.info(f"Parsed data: {data}")
        logger.info(f"Journal ID: {journal_id}")
        logger.info(f"AI Response length: {len(ai_response)}")
        logger.info(f"Response type: {response_type}")
        
        # Store in cache
        from django.core.cache import cache
        cache_key = f"ai_response_{journal_id}"
        
        ai_data = {
            'response': ai_response,
            'type': response_type,
            'timestamp': data.get('timestamp'),
            'received_at': timezone.now().isoformat()
        }
        
        logger.info(f"Storing in cache with key: {cache_key}")
        cache.set(cache_key, ai_data, timeout=3600)
        
        # Verify storage
        stored = cache.get(cache_key)
        if stored:
            logger.info(f"✓ Successfully stored in cache")
        else:
            logger.error(f"✗ Failed to store in cache")
        
        # Return success response to n8n
        return JsonResponse({
            'success': True,
            'message': 'AI response received successfully',
            'journal_id': journal_id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing AI response: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@login_required
def get_ai_response(request, journal_id):
    """
    Get AI response for a specific journal entry
    This will be called by JavaScript to check for AI responses
    """
    try:
        # Check if user owns this journal
        journal = get_object_or_404(JournalEntry, id=journal_id, author=request.user)
        
        # Get AI response from cache
        from django.core.cache import cache
        cache_key = f"ai_response_{journal_id}"
        ai_data = cache.get(cache_key)
        
        if ai_data:
            return JsonResponse({
                'success': True,
                'has_response': True,
                'ai_response': ai_data['response'],
                'response_type': ai_data['type'],
                'timestamp': ai_data.get('timestamp'),
                'received_at': ai_data.get('received_at')
            })
        else:
            return JsonResponse({
                'success': True,
                'has_response': False,
                'message': 'No AI response yet'
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)





@login_required
def delete_journal(request, pk):
    """
    Delete a journal entry
    Only the author can delete their own journal entries
    """
    journal = get_object_or_404(JournalEntry, id=pk, author=request.user)
    
    if request.method == 'POST':
        # Store journal title for success message
        journal_title = journal.title
        
        # Delete the journal (this will also delete related media files due to CASCADE)
        journal.delete()
        
        # Return JSON response for AJAX requests
        if request.headers.get('Content-Type') == 'application/json' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Journal "{journal_title}" has been deleted successfully.',
                'redirect_url': '/journal/'
            })
        
        # For regular form submissions, redirect to journal list
        from django.contrib import messages
        messages.success(request, f'Journal "{journal_title}" has been deleted successfully.')
        return redirect('journal-list')
    
    # For GET requests, show confirmation page
    return render(request, 'journal/delete_confirm.html', {
        'journal': journal
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
