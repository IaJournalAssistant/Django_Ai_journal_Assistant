from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import date, timedelta, datetime
from .models import Task, Project, Goal, TaskComment, AIInsight


class TaskModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.project = Project.objects.create(
            title='Test Project',
            user=self.user
        )
    
    def test_task_creation(self):
        """Test basic task creation with required fields"""
        task = Task.objects.create(
            title='Test Task',
            user=self.user
        )
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.user, self.user)
        self.assertEqual(task.status, 'pending')
        self.assertEqual(task.priority, 'medium')
        self.assertFalse(task.ai_suggested)
    
    def test_task_str_method(self):
        """Test task string representation"""
        task = Task.objects.create(title='Test Task', user=self.user)
        self.assertEqual(str(task), 'Test Task')
    
    def test_task_project_relationship(self):
        """Test task-project relationship"""
        task = Task.objects.create(
            title='Test Task',
            user=self.user,
            project=self.project
        )
        self.assertEqual(task.project, self.project)
        self.assertIn(task, self.project.tasks.all())
    
    def test_mark_completed_method(self):
        """Test marking task as completed"""
        task = Task.objects.create(title='Test Task', user=self.user)
        self.assertIsNone(task.completed_at)
        
        task.mark_completed()
        self.assertEqual(task.status, 'completed')
        self.assertIsNotNone(task.completed_at)
    
    def test_mark_in_progress_method(self):
        """Test marking task as in progress"""
        task = Task.objects.create(title='Test Task', user=self.user)
        task.mark_in_progress()
        self.assertEqual(task.status, 'in_progress')
    
    def test_is_overdue_method(self):
        """Test overdue detection"""
        # Task without due date should not be overdue
        task = Task.objects.create(title='Test Task', user=self.user)
        self.assertFalse(task.is_overdue())
        
        # Task with future due date should not be overdue
        future_date = timezone.now() + timedelta(days=1)
        task.due_date = future_date
        task.save()
        self.assertFalse(task.is_overdue())
        
        # Task with past due date should be overdue
        past_date = timezone.now() - timedelta(days=1)
        task.due_date = past_date
        task.save()
        self.assertTrue(task.is_overdue())
        
        # Completed task should not be overdue even if past due
        task.mark_completed()
        self.assertFalse(task.is_overdue())
    
    def test_get_progress_status_method(self):
        """Test progress status calculation"""
        task = Task.objects.create(title='Test Task', user=self.user)
        
        # Pending task
        self.assertEqual(task.get_progress_status(), 'Pending')
        
        # In progress task
        task.mark_in_progress()
        self.assertEqual(task.get_progress_status(), 'In Progress')
        
        # Completed task
        task.mark_completed()
        self.assertEqual(task.get_progress_status(), 'Completed')
        
        # Overdue task
        task.status = 'pending'
        task.due_date = timezone.now() - timedelta(days=1)
        task.save()
        self.assertEqual(task.get_progress_status(), 'Overdue')
    
    def test_task_cascade_delete_with_user(self):
        """Test that tasks are deleted when user is deleted"""
        task = Task.objects.create(title='Test Task', user=self.user)
        task_id = task.id
        
        self.user.delete()
        self.assertFalse(Task.objects.filter(id=task_id).exists())
    
    def test_task_project_set_null_on_delete(self):
        """Test that task project is set to null when project is deleted"""
        task = Task.objects.create(
            title='Test Task',
            user=self.user,
            project=self.project
        )
        
        self.project.delete()
        task.refresh_from_db()
        self.assertIsNone(task.project)


class ProjectModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_project_creation(self):
        """Test basic project creation"""
        project = Project.objects.create(
            title='Test Project',
            user=self.user
        )
        self.assertEqual(project.title, 'Test Project')
        self.assertEqual(project.user, self.user)
        self.assertEqual(project.status, 'active')
        self.assertEqual(project.progress_percentage, 0)
    
    def test_project_str_method(self):
        """Test project string representation"""
        project = Project.objects.create(title='Test Project', user=self.user)
        self.assertEqual(str(project), 'Test Project')
    
    def test_calculate_progress_from_tasks(self):
        """Test progress calculation from tasks"""
        project = Project.objects.create(title='Test Project', user=self.user)
        
        # No tasks should return 0%
        self.assertEqual(project.calculate_progress_from_tasks(), 0)
        
        # Create tasks
        task1 = Task.objects.create(title='Task 1', user=self.user, project=project)
        task2 = Task.objects.create(title='Task 2', user=self.user, project=project)
        task3 = Task.objects.create(title='Task 3', user=self.user, project=project)
        
        # No completed tasks should be 0%
        self.assertEqual(project.calculate_progress_from_tasks(), 0)
        
        # Complete one task (33%)
        task1.mark_completed()
        self.assertEqual(project.calculate_progress_from_tasks(), 33)
        
        # Complete second task (66%)
        task2.mark_completed()
        self.assertEqual(project.calculate_progress_from_tasks(), 66)
        
        # Complete all tasks (100%)
        task3.mark_completed()
        self.assertEqual(project.calculate_progress_from_tasks(), 100)
    
    def test_update_progress_method(self):
        """Test progress update method"""
        project = Project.objects.create(title='Test Project', user=self.user)
        task = Task.objects.create(title='Task 1', user=self.user, project=project)
        
        project.update_progress()
        self.assertEqual(project.progress_percentage, 0)
        
        task.mark_completed()
        project.update_progress()
        self.assertEqual(project.progress_percentage, 100)
    
    def test_mark_completed_method(self):
        """Test marking project as completed"""
        project = Project.objects.create(title='Test Project', user=self.user)
        self.assertIsNone(project.completed_at)
        
        project.mark_completed()
        self.assertEqual(project.status, 'completed')
        self.assertEqual(project.progress_percentage, 100)
        self.assertIsNotNone(project.completed_at)
    
    def test_get_task_counts_method(self):
        """Test task count calculation"""
        project = Project.objects.create(title='Test Project', user=self.user)
        
        # No tasks
        counts = project.get_task_counts()
        expected = {'total': 0, 'completed': 0, 'in_progress': 0, 'pending': 0}
        self.assertEqual(counts, expected)
        
        # Create tasks with different statuses
        Task.objects.create(title='Task 1', user=self.user, project=project, status='pending')
        Task.objects.create(title='Task 2', user=self.user, project=project, status='in_progress')
        Task.objects.create(title='Task 3', user=self.user, project=project, status='completed')
        
        counts = project.get_task_counts()
        expected = {'total': 3, 'completed': 1, 'in_progress': 1, 'pending': 1}
        self.assertEqual(counts, expected)
    
    def test_is_overdue_method(self):
        """Test project overdue detection"""
        project = Project.objects.create(title='Test Project', user=self.user)
        
        # No target date should not be overdue
        self.assertFalse(project.is_overdue())
        
        # Future target date should not be overdue
        future_date = date.today() + timedelta(days=1)
        project.target_completion_date = future_date
        project.save()
        self.assertFalse(project.is_overdue())
        
        # Past target date should be overdue
        past_date = date.today() - timedelta(days=1)
        project.target_completion_date = past_date
        project.save()
        self.assertTrue(project.is_overdue())
        
        # Completed project should not be overdue
        project.mark_completed()
        self.assertFalse(project.is_overdue())
    
    def test_project_cascade_delete_with_user(self):
        """Test that projects are deleted when user is deleted"""
        project = Project.objects.create(title='Test Project', user=self.user)
        project_id = project.id
        
        self.user.delete()
        self.assertFalse(Project.objects.filter(id=project_id).exists())


class GoalModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.target_date = date.today() + timedelta(days=30)
    
    def test_goal_creation(self):
        """Test basic goal creation"""
        goal = Goal.objects.create(
            title='Test Goal',
            user=self.user,
            success_criteria='Complete all tasks',
            target_date=self.target_date
        )
        self.assertEqual(goal.title, 'Test Goal')
        self.assertEqual(goal.user, self.user)
        self.assertEqual(goal.status, 'active')
        self.assertEqual(goal.progress_percentage, 0)
    
    def test_goal_str_method(self):
        """Test goal string representation"""
        goal = Goal.objects.create(
            title='Test Goal',
            user=self.user,
            success_criteria='Complete all tasks',
            target_date=self.target_date
        )
        self.assertEqual(str(goal), 'Test Goal')
    
    def test_update_progress_method(self):
        """Test progress update method"""
        goal = Goal.objects.create(
            title='Test Goal',
            user=self.user,
            success_criteria='Complete all tasks',
            target_date=self.target_date
        )
        
        # Valid progress update
        goal.update_progress(50)
        self.assertEqual(goal.progress_percentage, 50)
        self.assertEqual(goal.status, 'active')
        
        # Invalid progress (should not update)
        original_progress = goal.progress_percentage
        goal.update_progress(150)  # Invalid: > 100
        self.assertEqual(goal.progress_percentage, original_progress)
        
        goal.update_progress(-10)  # Invalid: < 0
        self.assertEqual(goal.progress_percentage, original_progress)
        
        # 100% should auto-mark as achieved
        goal.update_progress(100)
        self.assertEqual(goal.progress_percentage, 100)
        self.assertEqual(goal.status, 'achieved')
        self.assertIsNotNone(goal.achieved_at)
    
    def test_mark_achieved_method(self):
        """Test marking goal as achieved"""
        goal = Goal.objects.create(
            title='Test Goal',
            user=self.user,
            success_criteria='Complete all tasks',
            target_date=self.target_date
        )
        
        goal.mark_achieved()
        self.assertEqual(goal.status, 'achieved')
        self.assertEqual(goal.progress_percentage, 100)
        self.assertIsNotNone(goal.achieved_at)
    
    def test_is_overdue_method(self):
        """Test goal overdue detection"""
        # Future target date should not be overdue
        future_date = date.today() + timedelta(days=1)
        goal = Goal.objects.create(
            title='Test Goal',
            user=self.user,
            success_criteria='Complete all tasks',
            target_date=future_date
        )
        self.assertFalse(goal.is_overdue())
        
        # Past target date should be overdue
        past_date = date.today() - timedelta(days=1)
        goal.target_date = past_date
        goal.save()
        self.assertTrue(goal.is_overdue())
        
        # Achieved goal should not be overdue
        goal.mark_achieved()
        self.assertFalse(goal.is_overdue())
    
    def test_days_until_target_method(self):
        """Test days until target calculation"""
        future_date = date.today() + timedelta(days=5)
        goal = Goal.objects.create(
            title='Test Goal',
            user=self.user,
            success_criteria='Complete all tasks',
            target_date=future_date
        )
        
        self.assertEqual(goal.days_until_target(), 5)
        
        # Past date should return negative days
        past_date = date.today() - timedelta(days=3)
        goal.target_date = past_date
        goal.save()
        self.assertEqual(goal.days_until_target(), -3)
    
    def test_get_progress_status_method(self):
        """Test progress status calculation"""
        goal = Goal.objects.create(
            title='Test Goal',
            user=self.user,
            success_criteria='Complete all tasks',
            target_date=self.target_date
        )
        
        # Just started (0-24%)
        self.assertEqual(goal.get_progress_status(), 'Just Started')
        
        # Some progress (25-49%)
        goal.update_progress(30)
        self.assertEqual(goal.get_progress_status(), 'Some Progress')
        
        # Good progress (50-74%)
        goal.update_progress(60)
        self.assertEqual(goal.get_progress_status(), 'Good Progress')
        
        # Nearly complete (75-99%)
        goal.progress_percentage = 80
        goal.save()
        self.assertEqual(goal.get_progress_status(), 'Nearly Complete')
        
        # Achieved (100%)
        goal.mark_achieved()
        self.assertEqual(goal.get_progress_status(), 'Achieved')
        
        # Paused
        goal.status = 'paused'
        goal.save()
        self.assertEqual(goal.get_progress_status(), 'Paused')
        
        # Overdue
        goal.status = 'active'
        goal.target_date = date.today() - timedelta(days=1)
        goal.save()
        self.assertEqual(goal.get_progress_status(), 'Overdue')
    
    def test_goal_cascade_delete_with_user(self):
        """Test that goals are deleted when user is deleted"""
        goal = Goal.objects.create(
            title='Test Goal',
            user=self.user,
            success_criteria='Complete all tasks',
            target_date=self.target_date
        )
        goal_id = goal.id
        
        self.user.delete()
        self.assertFalse(Goal.objects.filter(id=goal_id).exists())


class TaskCommentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.task = Task.objects.create(
            title='Test Task',
            user=self.user
        )
    
    def test_comment_creation(self):
        """Test basic comment creation"""
        comment = TaskComment.objects.create(
            task=self.task,
            user=self.user,
            content='This is a test comment'
        )
        self.assertEqual(comment.task, self.task)
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.content, 'This is a test comment')
    
    def test_comment_str_method(self):
        """Test comment string representation"""
        comment = TaskComment.objects.create(
            task=self.task,
            user=self.user,
            content='Test comment'
        )
        expected = f"Comment on {self.task.title} by {self.user.username}"
        self.assertEqual(str(comment), expected)
    
    def test_comment_task_relationship(self):
        """Test comment-task relationship"""
        comment = TaskComment.objects.create(
            task=self.task,
            user=self.user,
            content='Test comment'
        )
        self.assertIn(comment, self.task.comments.all())
    
    def test_comment_cascade_delete_with_task(self):
        """Test that comments are deleted when task is deleted"""
        comment = TaskComment.objects.create(
            task=self.task,
            user=self.user,
            content='Test comment'
        )
        comment_id = comment.id
        
        self.task.delete()
        self.assertFalse(TaskComment.objects.filter(id=comment_id).exists())
    
    def test_comment_cascade_delete_with_user(self):
        """Test that comments are deleted when user is deleted"""
        comment = TaskComment.objects.create(
            task=self.task,
            user=self.user,
            content='Test comment'
        )
        comment_id = comment.id
        
        self.user.delete()
        self.assertFalse(TaskComment.objects.filter(id=comment_id).exists())


class AIInsightModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.task = Task.objects.create(
            title='Test Task',
            user=self.user
        )
    
    def test_ai_insight_creation(self):
        """Test basic AI insight creation"""
        from django.contrib.contenttypes.models import ContentType
        
        content_type = ContentType.objects.get_for_model(Task)
        insight = AIInsight.objects.create(
            user=self.user,
            content_type=content_type,
            object_id=self.task.id,
            insight_type='task_suggestion',
            content='This task could be broken down into smaller steps'
        )
        
        self.assertEqual(insight.user, self.user)
        self.assertEqual(insight.content_object, self.task)
        self.assertEqual(insight.insight_type, 'task_suggestion')
        self.assertFalse(insight.is_dismissed)
        self.assertFalse(insight.is_applied)
    
    def test_ai_insight_str_method(self):
        """Test AI insight string representation"""
        from django.contrib.contenttypes.models import ContentType
        
        content_type = ContentType.objects.get_for_model(Task)
        insight = AIInsight.objects.create(
            user=self.user,
            content_type=content_type,
            object_id=self.task.id,
            insight_type='task_suggestion',
            content='Test insight'
        )
        
        expected = f"Task Suggestion for {self.user.username}"
        self.assertEqual(str(insight), expected)
    
    def test_dismiss_method(self):
        """Test dismissing an insight"""
        from django.contrib.contenttypes.models import ContentType
        
        content_type = ContentType.objects.get_for_model(Task)
        insight = AIInsight.objects.create(
            user=self.user,
            content_type=content_type,
            object_id=self.task.id,
            insight_type='task_suggestion',
            content='Test insight'
        )
        
        insight.dismiss()
        self.assertTrue(insight.is_dismissed)
    
    def test_apply_method(self):
        """Test applying an insight"""
        from django.contrib.contenttypes.models import ContentType
        
        content_type = ContentType.objects.get_for_model(Task)
        insight = AIInsight.objects.create(
            user=self.user,
            content_type=content_type,
            object_id=self.task.id,
            insight_type='task_suggestion',
            content='Test insight'
        )
        
        insight.apply()
        self.assertTrue(insight.is_applied)
    
    def test_ai_insight_cascade_delete_with_user(self):
        """Test that AI insights are deleted when user is deleted"""
        from django.contrib.contenttypes.models import ContentType
        
        content_type = ContentType.objects.get_for_model(Task)
        insight = AIInsight.objects.create(
            user=self.user,
            content_type=content_type,
            object_id=self.task.id,
            insight_type='task_suggestion',
            content='Test insight'
        )
        insight_id = insight.id
        
        self.user.delete()
        self.assertFalse(AIInsight.objects.filter(id=insight_id).exists())