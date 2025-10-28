from django.urls import path
from . import views

urlpatterns = [
    # HTML upload page
    path('upload/<int:journal_id>/', views.upload_media, name='media-upload'),
]
