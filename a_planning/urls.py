"""
URL configuration for the Task & Project Planning module
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import (
    TaskViewSet, ProjectViewSet, GoalViewSet, 
    TaskCommentViewSet, AIInsightViewSet
)
from . import views

# Create a router and register our viewsets with different basenames to avoid conflicts
router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='api-task')
router.register(r'projects', ProjectViewSet, basename='api-project')
router.register(r'goals', GoalViewSet, basename='api-goal')
router.register(r'comments', TaskCommentViewSet, basename='api-taskcomment')
router.register(r'insights', AIInsightViewSet, basename='api-aiinsight')

app_name = 'planning'

urlpatterns = [
    # Web Interface URLs
    path('', views.dashboard_view, name='dashboard'),
    
    # Task URLs
    path('tasks/', views.task_list_view, name='task-list'),
    path('tasks/create/', views.task_create_view, name='task-create'),
    path('tasks/<int:task_id>/', views.task_detail_view, name='task-detail'),
    path('tasks/<int:task_id>/edit/', views.task_edit_view, name='task-edit'),
    path('tasks/<int:task_id>/delete/', views.task_delete_view, name='task-delete'),
    path('tasks/<int:task_id>/add-comment/', views.task_add_comment_view, name='task-add-comment'),
    
    # Project URLs
    path('projects/', views.project_list_view, name='project-list'),
    path('projects/create/', views.project_create_view, name='project-create'),
    path('projects/<int:project_id>/', views.project_detail_view, name='project-detail'),
    path('projects/<int:project_id>/edit/', views.project_edit_view, name='project-edit'),
    path('projects/<int:project_id>/mark-completed/', views.project_mark_completed_view, name='project-mark-completed'),
    path('projects/<int:project_id>/pause/', views.project_pause_view, name='project-pause'),
    path('projects/<int:project_id>/resume/', views.project_resume_view, name='project-resume'),
    path('projects/<int:project_id>/delete/', views.project_delete_view, name='project-delete'),
    
    # Goal URLs
    path('goals/', views.goal_list_view, name='goal-list'),
    path('goals/create/', views.goal_create_view, name='goal-create'),
    path('goals/<int:goal_id>/', views.goal_detail_view, name='goal-detail'),
    path('goals/<int:goal_id>/edit/', views.goal_edit_view, name='goal-edit'),
    path('goals/<int:goal_id>/mark-achieved/', views.goal_mark_achieved_view, name='goal-mark-achieved'),
    path('goals/<int:goal_id>/pause/', views.goal_pause_view, name='goal-pause'),
    path('goals/<int:goal_id>/resume/', views.goal_resume_view, name='goal-resume'),
    path('goals/<int:goal_id>/delete/', views.goal_delete_view, name='goal-delete'),
    
    # HTMX endpoints for dynamic updates
    path('htmx/tasks/<int:task_id>/toggle-status/', views.task_toggle_status, name='task-toggle-status'),
    path('htmx/projects/<int:project_id>/update-progress/', views.project_update_progress, name='project-update-progress'),
    path('htmx/goals/<int:goal_id>/update-progress/', views.goal_update_progress, name='goal-update-progress'),
    
    # AI-powered endpoints using n8n integration
    path('ai/task-summary/', views.ai_task_summary_view, name='ai-task-summary'),
    path('ai/project-analysis/<int:project_id>/', views.ai_project_analysis_view, name='ai-project-analysis'),
    path('ai/task-breakdown/', views.ai_task_breakdown_view, name='ai-task-breakdown'),
    path('ai/goal-action-plan/<int:goal_id>/', views.ai_goal_action_plan_view, name='ai-goal-action-plan'),
    path('ai/productivity-insights/', views.ai_productivity_insights_view, name='ai-productivity-insights'),
    
    # API endpoints
    path('api/', include(router.urls)),
]