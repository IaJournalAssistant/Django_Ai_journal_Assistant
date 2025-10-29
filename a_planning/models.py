from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Core fields
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    project = models.ForeignKey('Project', null=True, blank=True, on_delete=models.SET_NULL, related_name='tasks')
    
    # Status and priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # AI features
    ai_suggested = models.BooleanField(default=False)
    estimated_duration = models.DurationField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title
    
    def mark_completed(self):
        """Mark task as completed and set completion timestamp"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_in_progress(self):
        """Mark task as in progress"""
        self.status = 'in_progress'
        self.save()
    
    def is_overdue(self):
        """Check if task is overdue"""
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.due_date
        return False
    
    def get_progress_status(self):
        """Get human-readable progress status"""
        if self.status == 'completed':
            return 'Completed'
        elif self.is_overdue():
            return 'Overdue'
        elif self.status == 'in_progress':
            return 'In Progress'
        else:
            return 'Pending'


class Project(models.Model):
    PROJECT_STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Core fields
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    
    # Status and dates
    status = models.CharField(max_length=20, choices=PROJECT_STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_date = models.DateField(null=True, blank=True)
    target_completion_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Progress tracking
    progress_percentage = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title
    
    def calculate_progress_from_tasks(self):
        """Calculate project progress based on completed tasks"""
        total_tasks = self.tasks.count()
        if total_tasks == 0:
            return 0
        
        completed_tasks = self.tasks.filter(status='completed').count()
        return int((completed_tasks / total_tasks) * 100)
    
    def update_progress(self):
        """Update progress percentage based on task completion"""
        self.progress_percentage = self.calculate_progress_from_tasks()
        self.save()
    
    def mark_completed(self):
        """Mark project as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.progress_percentage = 100
        self.save()
    
    def get_task_counts(self):
        """Get counts of tasks by status"""
        return {
            'total': self.tasks.count(),
            'completed': self.tasks.filter(status='completed').count(),
            'in_progress': self.tasks.filter(status='in_progress').count(),
            'pending': self.tasks.filter(status='pending').count(),
        }
    
    def is_overdue(self):
        """Check if project is overdue"""
        if self.target_completion_date and self.status not in ['completed', 'cancelled']:
            return timezone.now().date() > self.target_completion_date
        return False


class Goal(models.Model):
    GOAL_STATUS_CHOICES = [
        ('active', 'Active'),
        ('achieved', 'Achieved'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Core fields
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    
    # Goal specifics
    success_criteria = models.TextField()
    target_date = models.DateField()
    progress_percentage = models.IntegerField(default=0)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=GOAL_STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    achieved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title
    
    def update_progress(self, percentage):
        """Update goal progress percentage"""
        if 0 <= percentage <= 100:
            self.progress_percentage = percentage
            self.updated_at = timezone.now()
            
            # Auto-mark as achieved if 100%
            if percentage == 100 and self.status != 'achieved':
                self.mark_achieved()
            else:
                self.save()
    
    def mark_achieved(self):
        """Mark goal as achieved"""
        self.status = 'achieved'
        self.progress_percentage = 100
        self.achieved_at = timezone.now()
        self.save()
    
    def is_overdue(self):
        """Check if goal is overdue"""
        if self.target_date and self.status not in ['achieved', 'cancelled']:
            return timezone.now().date() > self.target_date
        return False
    
    def days_until_target(self):
        """Calculate days until target date"""
        if self.target_date:
            delta = self.target_date - timezone.now().date()
            return delta.days
        return None
    
    def get_progress_status(self):
        """Get human-readable progress status"""
        if self.status == 'achieved':
            return 'Achieved'
        elif self.is_overdue():
            return 'Overdue'
        elif self.status == 'paused':
            return 'Paused'
        elif self.progress_percentage >= 75:
            return 'Nearly Complete'
        elif self.progress_percentage >= 50:
            return 'Good Progress'
        elif self.progress_percentage >= 25:
            return 'Some Progress'
        else:
            return 'Just Started'


class TaskComment(models.Model):
    """Comments on tasks for discussions and notes"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        
    def __str__(self):
        return f"Comment on {self.task.title} by {self.user.username}"


class AIInsight(models.Model):
    """AI-generated insights and suggestions for tasks, projects, and goals"""
    INSIGHT_TYPE_CHOICES = [
        ('task_suggestion', 'Task Suggestion'),
        ('project_planning', 'Project Planning'),
        ('goal_analysis', 'Goal Analysis'),
        ('productivity_tip', 'Productivity Tip'),
        ('priority_recommendation', 'Priority Recommendation'),
        ('timeline_suggestion', 'Timeline Suggestion'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_insights')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    insight_type = models.CharField(max_length=50, choices=INSIGHT_TYPE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_dismissed = models.BooleanField(default=False)
    is_applied = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.get_insight_type_display()} for {self.user.username}"
    
    def dismiss(self):
        """Mark insight as dismissed"""
        self.is_dismissed = True
        self.save()
    
    def apply(self):
        """Mark insight as applied"""
        self.is_applied = True
        self.save()