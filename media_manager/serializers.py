from rest_framework import serializers
from .models import MediaFile

class MediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = ['id', 'journal', 'uploaded_by', 'file', 'file_type', 'caption', 'created_at']
        read_only_fields = ['id', 'uploaded_by', 'created_at']
