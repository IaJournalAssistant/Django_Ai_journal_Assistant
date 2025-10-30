"""
API ViewSets for the Task & Project Planning module
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone

from .models import Task, Project, Goal, TaskComment, AIInsight
from .serializers import (
    TaskSerializer, TaskListSerializer, ProjectSerializer, ProjectListSerializer,
    GoalSerializer, TaskCommentSerializer, AIInsightSerializer
)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tasks via API
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'project']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'due_date', 'priority']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Task.objects.filter(user=self.request.user).select_related('project')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        return TaskSerializer
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Toggle task status between pending -> in_progress -> completed"""
        task = self.get_object()
        
        if task.status == 'pending':
            task.status = 'in_progress'
        elif task.status == 'in_progress':
            task.mark_completed()
        else:  # completed or cancelled
            task.status = 'pending'
            task.completed_at = None
        
        task.save()
        
        # Update project progress if task is in a project
        if task.project:
            task.project.update_progress()
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing projects via API
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'start_date', 'target_completion_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Project.objects.filter(user=self.request.user).prefetch_related('tasks')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectSerializer
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update project progress based on task completion"""
        project = self.get_object()
        project.update_progress()
        
        serializer = self.get_serializer(project)
        return Response(serializer.data)


class GoalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing goals via API
    """
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['title', 'description', 'success_criteria']
    ordering_fields = ['created_at', 'target_date', 'progress_percentage']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update goal progress percentage"""
        goal = self.get_object()
        percentage = request.data.get('percentage')
        
        if percentage is not None:
            try:
                percentage = int(percentage)
                if 0 <= percentage <= 100:
                    goal.update_progress(percentage)
                    serializer = self.get_serializer(goal)
                    return Response(serializer.data)
                else:
                    return Response(
                        {'error': 'Percentage must be between 0 and 100'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Invalid percentage value'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            {'error': 'Percentage is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


class TaskCommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing task comments via API
    """
    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['task']
    ordering = ['created_at']
    
    def get_queryset(self):
        return TaskComment.objects.filter(user=self.request.user).select_related('task', 'user')


class AIInsightViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing AI insights via API
    """
    serializer_class = AIInsightSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['insight_type', 'is_applied', 'is_dismissed']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return AIInsight.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Mark an AI insight as applied"""
        insight = self.get_object()
        insight.apply_insight()
        
        serializer = self.get_serializer(insight)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """Mark an AI insight as dismissed"""
        insight = self.get_object()
        insight.is_dismissed = True
        insight.save()
        
        serializer = self.get_serializer(insight)
        return Response(serializer.data)