from django.urls import path
from . import views

app_name = 'mood_tracker'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Mood Entry URLs
    path('mood/', views.mood_log, name='mood_log'),
    path('mood/edit/<int:pk>/', views.mood_edit, name='mood_edit'),
    path('mood/delete/<int:pk>/', views.mood_delete, name='mood_delete'),
    path('mood/history/', views.mood_history, name='mood_history'),
    
    # Habit URLs
    path('habits/', views.habit_list, name='habit_list'),
    path('habits/create/', views.habit_create, name='habit_create'),
    path('habits/edit/<int:pk>/', views.habit_edit, name='habit_edit'),
    path('habits/delete/<int:pk>/', views.habit_delete, name='habit_delete'),
    path('habits/toggle/<int:habit_id>/', views.habit_toggle, name='habit_toggle'),
    
    # Analytics and Insights
    path('insights/', views.insights, name='insights'),
    path('insights/generate/', views.generate_insights, name='generate_insights'),
    path('insights/correlation/', views.generate_correlation_insights, name='generate_correlation_insights'),
    path('insights/<int:insight_id>/', views.insight_detail, name='insight_detail'),
    path('insights/<int:insight_id>/archive/', views.archive_insight, name='archive_insight'),
    path('analytics/', views.analytics, name='analytics'),
    
    # API endpoints for HTMX/AJAX
    path('api/mood-chart-data/', views.mood_chart_data, name='mood_chart_data'),
    path('api/mood-calendar-data/', views.mood_calendar_data, name='mood_calendar_data'),
    path('api/habit-stats/<int:habit_id>/', views.habit_stats, name='habit_stats'),
    path('api/habit-heatmap/<int:habit_id>/', views.habit_heatmap_data, name='habit_heatmap_data'),
]