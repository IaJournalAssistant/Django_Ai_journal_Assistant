from django.db import models
from django.conf import settings 
from journal.models import JournalEntry

class MediaFile(models.Model):

    FILE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('document', 'Document'),
        ('other', 'Other'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to='media_files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='media_files', null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.file.name} uploaded by {self.user.username}"
