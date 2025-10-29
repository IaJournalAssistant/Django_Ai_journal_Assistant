#!/usr/bin/env python
"""
Script to create sample data for testing the Task & Project Planning module
"""
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'a_core.settings')
django.setup()

from django.contrib.auth.models import User
from a_planning.models import Task, Project, Goal, TaskComment, AIInsight
from django.contrib.contenttypes.models import ContentType


def create_sample_data():
    """Create sample tasks, projects, goals, and related data"""
    
    # Create test users (if they don't exist)
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    test_user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    print(f"✅ Users created/verified: {admin_user.username}, {test_user.username}")
    
    # Create sample projects
    projects_data = [
        {
            'title': 'Website Redesign',
            'description': 'Complete redesign of company website with modern UI/UX',
            'user': admin_user,
            'status': 'active',
            'start_date': timezone.now().date(),
            'target_completion_date': timezone.now().date() + timedelta(days=60)
        },
        {
            'title': 'Mobile App Development',
            'description': 'Develop cross-platform mobile application',
            'user': test_user,
            'status': 'active',
            'start_date': timezone.now().date() - timedelta(days=10),
            'target_completion_date': timezone.now().date() + timedelta(days=90)
        },
        {
            'title': 'Marketing Campaign Q4',
            'description': 'Launch comprehensive marketing campaign for Q4',
            'user': admin_user,
            'status': 'completed',
            'start_date': timezone.now().date() - timedelta(days=30),
            'target_completion_date': timezone.now().date() - timedelta(days=5),
            'completed_at': timezone.now() - timedelta(days=5),
            'progress_percentage': 100
        }
    ]
    
    projects = []
    for project_data in projects_data:
        project, created = Project.objects.get_or_create(
            title=project_data['title'],
            user=project_data['user'],
            defaults=project_data
        )
        projects.append(project)
        print(f"✅ Project {'created' if created else 'exists'}: {project.title}")
    
    # Create sample tasks
    tasks_data = [
        # Website Redesign Project Tasks
        {
            'title': 'Design wireframes',
            'description': 'Create detailed wireframes for all main pages',
            'user': admin_user,
            'project': projects[0],
            'status': 'completed',
            'priority': 'high',
            'due_date': timezone.now() + timedelta(days=7),
            'ai_suggested': False,
            'estimated_duration': timedelta(hours=16)
        },
        {
            'title': 'Develop homepage',
            'description': 'Code the new homepage with responsive design',
            'user': admin_user,
            'project': projects[0],
            'status': 'in_progress',
            'priority': 'high',
            'due_date': timezone.now() + timedelta(days=14),
            'ai_suggested': True,
            'estimated_duration': timedelta(hours=24)
        },
        {
            'title': 'Content migration',
            'description': 'Migrate existing content to new structure',
            'user': admin_user,
            'project': projects[0],
            'status': 'pending',
            'priority': 'medium',
            'due_date': timezone.now() + timedelta(days=21),
            'ai_suggested': True,
            'estimated_duration': timedelta(hours=12)
        },
        
        # Mobile App Development Tasks
        {
            'title': 'Setup development environment',
            'description': 'Configure React Native development environment',
            'user': test_user,
            'project': projects[1],
            'status': 'completed',
            'priority': 'urgent',
            'due_date': timezone.now() + timedelta(days=3),
            'ai_suggested': False,
            'estimated_duration': timedelta(hours=8),
            'completed_at': timezone.now() - timedelta(days=2)
        },
        {
            'title': 'Design app architecture',
            'description': 'Plan the overall architecture and data flow',
            'user': test_user,
            'project': projects[1],
            'status': 'in_progress',
            'priority': 'high',
            'due_date': timezone.now() + timedelta(days=10),
            'ai_suggested': True,
            'estimated_duration': timedelta(hours=20)
        },
        
        # Standalone tasks (no project)
        {
            'title': 'Weekly team meeting',
            'description': 'Attend weekly team standup meeting',
            'user': admin_user,
            'project': None,
            'status': 'pending',
            'priority': 'low',
            'due_date': timezone.now() + timedelta(days=2),
            'ai_suggested': False,
            'estimated_duration': timedelta(hours=1)
        },
        {
            'title': 'Code review for PR #123',
            'description': 'Review pull request for authentication module',
            'user': test_user,
            'project': None,
            'status': 'pending',
            'priority': 'medium',
            'due_date': timezone.now() + timedelta(days=1),
            'ai_suggested': True,
            'estimated_duration': timedelta(hours=2)
        }
    ]
    
    tasks = []
    for task_data in tasks_data:
        task, created = Task.objects.get_or_create(
            title=task_data['title'],
            user=task_data['user'],
            defaults=task_data
        )
        tasks.append(task)
        print(f"✅ Task {'created' if created else 'exists'}: {task.title}")
    
    # Create sample goals
    goals_data = [
        {
            'title': 'Learn Django Advanced Features',
            'description': 'Master advanced Django concepts including custom managers, signals, and optimization',
            'user': admin_user,
            'success_criteria': 'Complete 3 advanced Django projects and pass certification exam',
            'target_date': timezone.now().date() + timedelta(days=120),
            'progress_percentage': 35,
            'status': 'active'
        },
        {
            'title': 'Improve Team Productivity',
            'description': 'Implement tools and processes to increase team productivity by 25%',
            'user': test_user,
            'success_criteria': 'Achieve 25% reduction in project delivery time and 90% team satisfaction',
            'target_date': timezone.now().date() + timedelta(days=90),
            'progress_percentage': 60,
            'status': 'active'
        },
        {
            'title': 'Complete React Native Course',
            'description': 'Finish comprehensive React Native development course',
            'user': test_user,
            'success_criteria': 'Complete all modules and build 2 production-ready apps',
            'target_date': timezone.now().date() + timedelta(days=45),
            'progress_percentage': 100,
            'status': 'achieved',
            'achieved_at': timezone.now() - timedelta(days=2)
        }
    ]
    
    goals = []
    for goal_data in goals_data:
        goal, created = Goal.objects.get_or_create(
            title=goal_data['title'],
            user=goal_data['user'],
            defaults=goal_data
        )
        goals.append(goal)
        print(f"✅ Goal {'created' if created else 'exists'}: {goal.title}")
    
    # Create sample task comments
    comments_data = [
        {
            'task': tasks[1],  # Develop homepage
            'user': admin_user,
            'content': 'Started working on the responsive grid system. Making good progress!'
        },
        {
            'task': tasks[1],
            'user': test_user,
            'content': 'Looks great! Consider using CSS Grid for better browser support.'
        },
        {
            'task': tasks[4],  # Design app architecture
            'user': test_user,
            'content': 'Researching Redux vs Context API for state management.'
        }
    ]
    
    for comment_data in comments_data:
        comment, created = TaskComment.objects.get_or_create(
            task=comment_data['task'],
            user=comment_data['user'],
            content=comment_data['content']
        )
        print(f"✅ Comment {'created' if created else 'exists'} for task: {comment.task.title}")
    
    # Create sample AI insights
    task_content_type = ContentType.objects.get_for_model(Task)
    project_content_type = ContentType.objects.get_for_model(Project)
    
    insights_data = [
        {
            'user': admin_user,
            'content_type': task_content_type,
            'object_id': tasks[2].id,  # Content migration task
            'insight_type': 'task_suggestion',
            'content': 'Consider breaking this task into smaller chunks: 1) Audit existing content, 2) Create migration plan, 3) Execute migration, 4) Validate results.',
            'is_applied': False,
            'is_dismissed': False
        },
        {
            'user': test_user,
            'content_type': project_content_type,
            'object_id': projects[1].id,  # Mobile App Development
            'insight_type': 'project_planning',
            'content': 'Based on similar projects, consider adding these tasks: User authentication, Push notifications, Offline data sync, App store optimization.',
            'is_applied': True,
            'is_dismissed': False
        },
        {
            'user': admin_user,
            'content_type': task_content_type,
            'object_id': tasks[6].id,  # Code review task
            'insight_type': 'priority_recommendation',
            'content': 'This code review is blocking other team members. Consider increasing priority to High.',
            'is_applied': False,
            'is_dismissed': False
        }
    ]
    
    for insight_data in insights_data:
        insight, created = AIInsight.objects.get_or_create(
            user=insight_data['user'],
            content_type=insight_data['content_type'],
            object_id=insight_data['object_id'],
            insight_type=insight_data['insight_type'],
            defaults=insight_data
        )
        print(f"✅ AI Insight {'created' if created else 'exists'}: {insight.insight_type}")
    
    # Update project progress based on tasks
    for project in projects:
        project.update_progress()
        print(f"✅ Updated progress for project: {project.title} ({project.progress_percentage}%)")
    
    print("\n🎉 Sample data creation completed!")
    print(f"📊 Summary:")
    print(f"   - Users: {User.objects.count()}")
    print(f"   - Projects: {Project.objects.count()}")
    print(f"   - Tasks: {Task.objects.count()}")
    print(f"   - Goals: {Goal.objects.count()}")
    print(f"   - Comments: {TaskComment.objects.count()}")
    print(f"   - AI Insights: {AIInsight.objects.count()}")
    print(f"\n🌐 Access the admin interface at: http://127.0.0.1:8000/admin/")
    print(f"   Username: admin")
    print(f"   Password: admin")


if __name__ == "__main__":
    create_sample_data()