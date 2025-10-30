from django.urls import path
from . import views

app_name = 'chatbotmedia'

urlpatterns = [
    path("images/", views.analyze_image, name="analyze_image"),
]
