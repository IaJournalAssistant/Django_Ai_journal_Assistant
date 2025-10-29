"""
Serializers for the Task & Project Planning API
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, Project, Goal, TaskComment, AIInsight


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model (read-only for API responses)"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id', 'username', 'first_name', 'last_name', 'email']


class TaskCommentSerializer(serializers.ModelSerializer):
    """Serializer for TaskComment model"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = TaskComment
        fields = ['id', 'user', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        """Set the user from the request context"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model with full CRUD support"""
    user = UserSerializer(read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    progress_status = serializers.CharField(source='get_progress_status', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'user', 'project', 'project_title',
            'status', 'priority', 'created_at', 'updated_at', 'due_date', 
            'completed_at', 'ai_suggested', 'estimated_duration', 'comments',
            'progress_status', 'is_overdue'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'completed_at']
    
    def create(self, validated_data):
        """Set the user from the request context"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_due_date(self, value):
        """Validate that due date is not in the past for new tasks"""
        if value and self.instance is None:  # Only for new tasks
            from django.utils import timezone
            if value < timezone.now():
                raise serializers.ValidationError("Due date cannot be in the past.")
        return value
    
    def validate_estimated_duration(self, value):
        """Validate estimated duration is reasonable"""
        if value:
            from datetime import timedelta
            if value > timedelta(days=365):
                raise serializers.ValidationError("Estimated duration cannot exceed 1 year.")
            if value <= timedelta(0):
                raise serializers.ValidationError("Estimated duration must be positive.")
        return value


class TaskListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for task lists"""
    user = serializers.CharField(source='user.username', read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    progress_status = serializers.CharField(source='get_progress_status', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'user', 'project', 'project_title', 'status', 
            'priority', 'due_date', 'ai_suggested', 'progress_status', 'created_at'
        ]


class ProjectTaskSerializer(serializers.ModelSerializer):
    """Serializer for tasks within project context"""
    progress_status = serializers.CharField(source='get_progress_status', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority', 
            'due_date', 'completed_at', 'progress_status', 'created_at'
        ]


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model with task relationships"""
    user = UserSerializer(read_only=True)
    tasks = ProjectTaskSerializer(many=True, read_only=True)
    task_counts = serializers.SerializerMethodField()
    calculated_progress = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'user', 'status', 'created_at', 
            'updated_at', 'start_date', 'target_completion_date', 'completed_at',
            'progress_percentage', 'calculated_progress', 'tasks', 'task_counts', 'is_overdue'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'completed_at']
    
    def get_task_counts(self, obj):
        """Get task counts by status"""
        return obj.get_task_counts()
    
    def get_calculated_progress(self, obj):
        """Get progress calculated from tasks"""
        return obj.calculate_progress_from_tasks()
    
    def create(self, validated_data):
        """Set the user from the request context"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_target_completion_date(self, value):
        """Validate target completion date"""
        if value and self.instance is None:  # Only for new projects
            from django.utils import timezone
            if value < timezone.now().date():
                raise serializers.ValidationError("Target completion date cannot be in the past.")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        start_date = data.get('start_date')
        target_date = data.get('target_completion_date')
        
        if start_date and target_date and start_date > target_date:
            raise serializers.ValidationError({
                'target_completion_date': 'Target completion date must be after start date.'
            })
        
        return data


class ProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for project lists"""
    user = serializers.CharField(source='user.username', read_only=True)
    task_counts = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'user', 'status', 'start_date', 'target_completion_date',
            'progress_percentage', 'task_counts', 'created_at'
        ]
    
    def get_task_counts(self, obj):
        """Get task counts by status"""
        return obj.get_task_counts()


class GoalSerializer(serializers.ModelSerializer):
    """Serializer for Goal model"""
    user = UserSerializer(read_only=True)
    progress_status = serializers.CharField(source='get_progress_status', read_only=True)
    days_until_target = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Goal
        fields = [
            'id', 'title', 'description', 'user', 'success_criteria', 'target_date',
            'progress_percentage', 'status', 'created_at', 'updated_at', 'achieved_at',
            'progress_status', 'days_until_target', 'is_overdue'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'achieved_at']
    
    def create(self, validated_data):
        """Set the user from the request context"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_target_date(self, value):
        """Validate target date is not in the past for new goals"""
        if value and self.instance is None:  # Only for new goals
            from django.utils import timezone
            if value < timezone.now().date():
                raise serializers.ValidationError("Target date cannot be in the past.")
        return value
    
    def validate_progress_percentage(self, value):
        """Validate progress percentage is between 0 and 100"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Progress percentage must be between 0 and 100.")
        return value


class AIInsightSerializer(serializers.ModelSerializer):
    """Serializer for AIInsight model"""
    user = UserSerializer(read_only=True)
    content_object_str = serializers.CharField(source='__str__', read_only=True)
    
    class Meta:
        model = AIInsight
        fields = [
            'id', 'user', 'content_type', 'object_id', 'content_object_str',
            'insight_type', 'content', 'created_at', 'is_dismissed', 'is_applied'
        ]
        read_only_fields = ['id', 'user', 'created_at']
    
    def create(self, validated_data):
        """Set the user from the request context"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)