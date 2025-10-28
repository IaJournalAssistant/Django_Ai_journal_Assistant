from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from .views import MediaFileViewSet

router = DefaultRouter()

urlpatterns = [
    # HTML upload page
    path('journal/<int:journal_id>/upload/', views.media_upload, name='media-upload'),
    # API router
    path('', include(router.urls)),
]
