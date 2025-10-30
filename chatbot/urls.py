# chatbot/urls.py - CORRECTION COMPLÈTE
from django.urls import path
from . import views

urlpatterns = [
    # Page principale
    path('', views.chatbot_view, name='chatbot'),
    
    # API conversations
    path('api/conversations/', views.list_conversations, name='list_conversations'),
    path('api/conversations/create/', views.start_conversation, name='start_conversation'),
    path('api/conversations/<int:id>/', views.get_conversation, name='get_conversation'),
    path('api/conversations/<int:id>/delete/', views.delete_conversation, name='delete_conversation'),
    path('api/conversations/<int:id>/ai-response/', views.generate_ai_response_view, name='generate_ai_response'),
    
    # API réflexions
    path('api/reflections/', views.list_reflections, name='list_reflections'),
    path('api/reflections/create/', views.save_reflection, name='save_reflection'),
    path('api/reflections/<int:id>/', views.delete_reflection, name='delete_reflection'),
    path('api/reflections/prompt/', views.get_reflection_prompt, name='get_reflection_prompt'),
    path('api/reflections/guided/create/', views.save_guided_reflection, name='save_guided_reflection'),

    # Test
    path('api/test/', views.test_api, name='test_api'),
]