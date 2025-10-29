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
    ViewSet for Task model with full CRUD operations
    Provides filtering, searching, and pagination
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'project', 'ai_suggested']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'priority']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return tasks for the authenticated user only"""
        return Task.objects.filter(user=self.request.user).select_related('user', 'project')
    
    def get_serializer_class(self):
        """Use lightweight serializer for list view"""
        if self.action == 'list':
            return TaskListSerializer
        return TaskSerializer
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark a task as completed"""
        task = self.get_object()
        task.mark_completed()
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_in_progress(self, request, pk=None):
        """Mark a task as in progress"""
        task = self.get_object()
        task.mark_in_progress()
        serializer = self.get_serializer(task)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get all overdue tasks for the user"""
        overdue_tasks = [task for task in self.get_queryset() if task.is_overdue()]
        serializer = self.get_serializer(overdue_tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_priority(self, request):
        """Get tasks grouped by priority"""
        queryset = self.get_queryset()
        priorities = ['urgent', 'high', 'medium', 'low']
        
        result = {}
        for priority in priorities:
            tasks = queryset.filter(priority=priority)
            serializer = self.get_serializer(tasks, many=True)
            result[priority] = serializer.data
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def ai_suggested(self, request):
        """Get all AI-suggested tasks"""
        ai_tasks = self.get_queryset().filter(ai_suggested=True)
        serializer = self.get_serializer(ai_tasks, many=True)
        return Response(serializer.data)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Project model with task relationship management
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'start_date', 'target_completion_date', 'progress_percentage']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return projects for the authenticated user only"""
        return Project.objects.filter(user=self.request.user).prefetch_related('tasks')
    
    def get_serializer_class(self):
        """Use lightweight serializer for list view"""
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectSerializer
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Recalculate project progress from tasks"""
        project = self.get_object()
        project.update_progress()
        serializer = self.get_serializer(project)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark a project as completed"""
        project = self.get_object()
        project.mark_completed()
        serializer = self.get_serializer(project)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def assign_task(self, request, pk=None):
        """Assign a task to this project"""
        project = self.get_object()
        task_id = request.data.get('task_id')
        
        if not task_id:
            return Response(
                {'error': 'task_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            task = Task.objects.get(id=task_id, user=request.user)
            task.project = project
            task.save()
            
            # Update project progress
            project.update_progress()
            
            return Response({
                'message': f'Task "{task.title}" assigned to project "{project.title}"',
                'task_id': task.id,
                'project_progress': project.progress_percentage
            })
        except Task.DoesNotExist:
            return Response(
                {'error': 'Task not found or not owned by user'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_task(self, request, pk=None):
        """Remove a task from this project"""
        project = self.get_object()
        task_id = request.data.get('task_id')
        
        if not task_id:
            return Response(
                {'error': 'task_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            task = Task.objects.get(id=task_id, user=request.user, project=project)
            task.project = None
            task.save()
            
            # Update project progress
            project.update_progress()
            
            return Response({
                'message': f'Task "{task.title}" removed from project "{project.title}"',
                'task_id': task.id,
                'project_progress': project.progress_percentage
            })
        except Task.DoesNotExist:
            return Response(
                {'error': 'Task not found in this project'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """Get all tasks for this project"""
        project = self.get_object()
        tasks = project.tasks.all()
        serializer = TaskListSerializer(tasks, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active projects"""
        active_projects = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(active_projects, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get all overdue projects"""
        overdue_projects = [project for project in self.get_queryset() if project.is_overdue()]
        serializer = self.get_serializer(overdue_projects, many=True)
        return Response(serializer.data)


class GoalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Goal model with progress tracking
    """
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['title', 'description', 'success_criteria']
    ordering_fields = ['created_at', 'updated_at', 'target_date', 'progress_percentage']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return goals for the authenticated user only"""
        return Goal.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update goal progress percentage"""
        goal = self.get_object()
        percentage = request.data.get('percentage')
        
        if percentage is None:
            return Response(
                {'error': 'percentage is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            percentage = int(percentage)
            if percentage < 0 or percentage > 100:
                return Response(
                    {'error': 'percentage must be between 0 and 100'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            goal.update_progress(percentage)
            serializer = self.get_serializer(goal)
            return Response(serializer.data)
        except (ValueError, TypeError):
            return Response(
                {'error': 'percentage must be a valid integer'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def mark_achieved(self, request, pk=None):
        """Mark a goal as achieved"""
        goal = self.get_object()
        goal.mark_achieved()
        serializer = self.get_serializer(goal)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active goals"""
        active_goals = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(active_goals, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def achieved(self, request):
        """Get all achieved goals"""
        achieved_goals = self.get_queryset().filter(status='achieved')
        serializer = self.get_serializer(achieved_goals, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get all overdue goals"""
        overdue_goals = [goal for goal in self.get_queryset() if goal.is_overdue()]
        serializer = self.get_serializer(overdue_goals, many=True)
        return Response(serializer.data)


class TaskCommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TaskComment model
    """
    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['task']
    ordering = ['created_at']
    
    def get_queryset(self):
        """Return comments for tasks owned by the authenticated user"""
        return TaskComment.objects.filter(task__user=self.request.user).select_related('user', 'task')


class AIInsightViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AIInsight model
    """
    serializer_class = AIInsightSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['insight_type', 'is_applied', 'is_dismissed', 'content_type']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return AI insights for the authenticated user only"""
        return AIInsight.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Mark an AI insight as applied"""
        insight = self.get_object()
        insight.apply()
        serializer = self.get_serializer(insight)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """Mark an AI insight as dismissed"""
        insight = self.get_object()
        insight.dismiss()
        serializer = self.get_serializer(insight)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending (not applied or dismissed) insights"""
        pending_insights = self.get_queryset().filter(is_applied=False, is_dismissed=False)
        serializer = self.get_serializer(pending_insights, many=True)
        return Response(serializer.data)