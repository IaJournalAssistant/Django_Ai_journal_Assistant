from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import MediaUploadForm
from .models import MediaFile
from journal.models import JournalEntry
from .speech_to_text import process_audio_transcription


@login_required
def upload_media(request, journal_id):
    journal = get_object_or_404(JournalEntry, id=journal_id, author=request.user)
    
    if request.method == 'POST':
        form = MediaUploadForm(request.POST, request.FILES)
        if form.is_valid():
            media_file = form.save(commit=False)
            media_file.journal = journal
            media_file.uploaded_by = request.user
            media_file.save()
            return redirect('journal-detail', pk=journal.id)
    else:
        form = MediaUploadForm()

    media_items = journal.media_files.all()
    return render(request, 'media_manager/upload.html', {
        'form': form,
        'journal': journal,
        'media_items': media_items,
    })


@login_required
@require_POST
def transcribe_audio(request, media_id):
    """Manually trigger transcription for an audio file"""
    media_file = get_object_or_404(MediaFile, id=media_id, uploaded_by=request.user)
    
    if media_file.file_type != 'audio':
        return JsonResponse({
            'success': False,
            'error': 'File is not an audio file'
        }, status=400)
    
    # Process transcription
    success = process_audio_transcription(media_id)
    
    if success:
        media_file.refresh_from_db()
        return JsonResponse({
            'success': True,
            'transcription': media_file.transcription,
            'confidence': media_file.transcription_confidence,
            'status': media_file.transcription_status
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Transcription failed'
        }, status=500)


@login_required
def transcription_status(request, media_id):
    """Get transcription status for an audio file"""
    media_file = get_object_or_404(MediaFile, id=media_id, uploaded_by=request.user)
    
    return JsonResponse({
        'status': media_file.transcription_status,
        'transcription': media_file.transcription,
        'confidence': media_file.transcription_confidence,
        'has_transcription': bool(media_file.transcription)
    })