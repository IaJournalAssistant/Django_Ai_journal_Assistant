from django.db import models
from django.contrib.auth.models import User

class ImageEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/')
    extracted_text = models.TextField(blank=True, null=True)
    sentiment = models.CharField(max_length=50, blank=True, null=True)
    emotion = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ImageEntry {self.id} by {self.user.username}"
