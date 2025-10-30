from django.urls import path
from . import views

urlpatterns = [
    # HTML upload page
    path('upload/<int:journal_id>/', views.upload_media, name='media-upload'),
    
    # Speech-to-text endpoints
    path('transcribe/<int:media_id>/', views.transcribe_audio, name='transcribe-audio'),
    path('transcription-status/<int:media_id>/', views.transcription_status, name='transcription-status'),
]
