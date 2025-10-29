from django.db import models
from django.conf import settings 
from journal.models import JournalEntry

class MediaFile(models.Model):

    FILE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document'),
        ('other', 'Other'),
    ]
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to='media_files/')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='other')
    caption = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    journal = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='media_files', null=True, blank=True)
    
    # Speech-to-text fields (non-intrusive addition)
    transcription = models.TextField(blank=True, null=True, help_text="Auto-generated transcription for audio files")
    transcription_status = models.CharField(
        max_length=20, 
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending',
        help_text="Status of speech-to-text processing"
    )
    transcription_confidence = models.FloatField(null=True, blank=True, help_text="Confidence score of transcription")
    
    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.file.name} uploaded by {self.uploaded_by.username}"
