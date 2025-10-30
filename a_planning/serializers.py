"""
Serializers for the Task & Project Planning module API
"""
from rest_framework import serializers
from .models import Task, Project, Goal, TaskComment, AIInsight


class TaskListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for task lists"""
    project_title = serializers.CharField(source='project.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'status', 'status_display', 'priority', 'priority_display',
            'due_date', 'is_overdue', 'project', 'project_title', 'created_at', 'updated_at'
        ]


class TaskSerializer(serializers.ModelSerializer):
    """Full serializer for task details"""
    project_title = serializers.CharField(source='project.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'status_display', 'priority', 'priority_display',
            'due_date', 'is_overdue', 'estimated_duration', 'project', 'project_title',
            'ai_suggested', 'created_at', 'updated_at', 'completed_at', 'comments_count'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'completed_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for project lists"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    task_counts = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'status', 'status_display', 'progress_percentage',
            'start_date', 'target_completion_date', 'is_overdue', 'task_counts',
            'created_at', 'updated_at'
        ]
    
    def get_task_counts(self, obj):
        return obj.get_task_counts()


class ProjectSerializer(serializers.ModelSerializer):
    """Full serializer for project details"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    task_counts = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'status', 'status_display', 'progress_percentage',
            'start_date', 'target_completion_date', 'completed_at', 'is_overdue',
            'task_counts', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'completed_at', 'progress_percentage']
    
    def get_task_counts(self, obj):
        return obj.get_task_counts()
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class GoalSerializer(serializers.ModelSerializer):
    """Serializer for goals"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progress_status = serializers.CharField(source='get_progress_status', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    days_until_target = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Goal
        fields = [
            'id', 'title', 'description', 'success_criteria', 'status', 'status_display',
            'progress_percentage', 'progress_status', 'target_date', 'is_overdue',
            'days_until_target', 'achieved_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'achieved_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class TaskCommentSerializer(serializers.ModelSerializer):
    """Serializer for task comments"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = TaskComment
        fields = ['id', 'content', 'user', 'user_name', 'task', 'created_at']
        read_only_fields = ['user', 'created_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AIInsightSerializer(serializers.ModelSerializer):
    """Serializer for AI insights"""
    insight_type_display = serializers.CharField(source='get_insight_type_display', read_only=True)
    
    class Meta:
        model = AIInsight
        fields = [
            'id', 'content', 'insight_type', 'insight_type_display', 'confidence_score',
            'is_applied', 'is_dismissed', 'applied_at', 'created_at'
        ]
        read_only_fields = ['user', 'created_at', 'applied_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)