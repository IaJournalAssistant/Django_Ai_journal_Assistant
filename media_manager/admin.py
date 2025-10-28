from django.contrib import admin
from .models import MediaFile

@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'journal', 'file_type', 'uploaded_by', 'created_at')
    list_filter = ('file_type','created_at')
    search_fields = ('journal__title','caption','uploaded_by__username')
 