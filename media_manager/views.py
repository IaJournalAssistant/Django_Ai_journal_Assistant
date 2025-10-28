from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from .forms import MediaUploadForm
from .models import MediaFile
from journal.models import JournalEntry

@login_required
def upload_media(request, journal_id):
    journal = get_object_or_404(JournalEntry, id=journal_id, author=request.user)
    if journal.author != request.user:
        return render(request, '404.html', status=403)


    if request.method == 'POST':
        form = MediaUploadForm(request.POST, request.FILES)
        if form.is_valid():
            media_file = form.save(commit=False)
            media_file.journal = journal
            media_file.uploaded_by = request.user
            media_file.save()
            return redirect('journal-detail', journal_id=journal.id)
        else:
           form = MediaUploadForm()

        media_items = journal.media_files.all()
        return render(request, 'media_manager/upload.html', {
            'form': form,
            'journal': journal,
            'media_items': media_items,
        })