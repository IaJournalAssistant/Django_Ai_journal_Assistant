from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from a_planning.models import Project, Task, Goal
import random


class Command(BaseCommand):
    help = 'Populate the database with sample users, projects, tasks, and goals'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=3,
            help='Number of users to create (default: 3)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data population...'))
        
        # Create users
        users = self.create_users(options['users'])
        
        # Create projects for each user
        projects = []
        for user in users:
            user_projects = self.create_projects_for_user(user)
            projects.extend(user_projects)
        
        # Create tasks for projects and standalone tasks
        for user in users:
            self.create_tasks_for_user(user, projects)
        
        # Create goals for each user
        for user in users:
            self.create_goals_for_user(user)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated database with:\n'
                f'- {len(users)} users\n'
                f'- {len(projects)} projects\n'
                f'- {Task.objects.count()} tasks\n'
                f'- {Goal.objects.count()} goals'
            )
        )

    def create_users(self, count):
        users = []
        user_data = [
            {'username': 'john_doe', 'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Doe'},
            {'username': 'jane_smith', 'email': 'jane@example.com', 'first_name': 'Jane', 'last_name': 'Smith'},
            {'username': 'alex_wilson', 'email': 'alex@example.com', 'first_name': 'Alex', 'last_name': 'Wilson'},
            {'username': 'sarah_johnson', 'email': 'sarah@example.com', 'first_name': 'Sarah', 'last_name': 'Johnson'},
            {'username': 'mike_brown', 'email': 'mike@example.com', 'first_name': 'Mike', 'last_name': 'Brown'},
        ]
        
        for i in range(min(count, len(user_data))):
            data = user_data[i]
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'is_active': True,
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created user: {user.username}')
            else:
                self.stdout.write(f'User already exists: {user.username}')
            users.append(user)
        
        return users

    def create_projects_for_user(self, user):
        project_templates = [
            {
                'title': 'Website Redesign',
                'description': 'Complete overhaul of company website with modern design and improved UX',
                'status': 'active',
                'priority': 'high'
            },
            {
                'title': 'Mobile App Development',
                'description': 'Develop cross-platform mobile application for iOS and Android',
                'status': 'active',
                'priority': 'medium'
            },
            {
                'title': 'Marketing Campaign Q4',
                'description': 'Launch comprehensive marketing campaign for Q4 product releases',
                'status': 'planning',
                'priority': 'high'
            },
            {
                'title': 'Database Migration',
                'description': 'Migrate legacy database to new cloud infrastructure',
                'status': 'active',
                'priority': 'medium'
            },
            {
                'title': 'Team Training Program',
                'description': 'Implement comprehensive training program for new technologies',
                'status': 'planning',
                'priority': 'low'
            }
        ]
        
        projects = []
        # Create 2-3 projects per user
        selected_projects = random.sample(project_templates, random.randint(2, 3))
        
        for project_data in selected_projects:
            start_date = timezone.now().date() - timedelta(days=random.randint(1, 30))
            target_date = start_date + timedelta(days=random.randint(30, 90))
            
            project = Project.objects.create(
                title=project_data['title'],
                description=project_data['description'],
                user=user,
                status=project_data['status'],
                start_date=start_date,
                target_completion_date=target_date
            )
            projects.append(project)
            self.stdout.write(f'Created project: {project.title} for {user.username}')
        
        return projects

    def create_tasks_for_user(self, user, all_projects):
        # Get user's projects
        user_projects = [p for p in all_projects if p.user == user]
        
        task_templates = [
            {
                'title': 'Design wireframes',
                'description': 'Create detailed wireframes for all main pages',
                'priority': 'high',
                'status': 'completed'
            },
            {
                'title': 'Develop homepage',
                'description': 'Code the new homepage with responsive design',
                'priority': 'high',
                'status': 'in_progress'
            },
            {
                'title': 'Content migration',
                'description': 'Migrate existing content to new CMS',
                'priority': 'medium',
                'status': 'pending'
            },
            {
                'title': 'User testing',
                'description': 'Conduct user testing sessions with target audience',
                'priority': 'medium',
                'status': 'pending'
            },
            {
                'title': 'SEO optimization',
                'description': 'Optimize all pages for search engines',
                'priority': 'low',
                'status': 'pending'
            },
            {
                'title': 'Performance testing',
                'description': 'Test website performance and optimize loading times',
                'priority': 'medium',
                'status': 'pending'
            },
            {
                'title': 'Weekly team meeting',
                'description': 'Regular team sync and progress review',
                'priority': 'low',
                'status': 'pending'
            },
            {
                'title': 'Client presentation',
                'description': 'Present project progress to client stakeholders',
                'priority': 'high',
                'status': 'pending'
            }
        ]
        
        # Create tasks for projects
        for project in user_projects:
            project_tasks = random.sample(task_templates, random.randint(3, 5))
            for task_data in project_tasks:
                due_date = None
                if random.choice([True, False]):  # 50% chance of having due date
                    due_date = timezone.now().date() + timedelta(days=random.randint(1, 30))
                
                Task.objects.create(
                    title=task_data['title'],
                    description=task_data['description'],
                    user=user,
                    project=project,
                    priority=task_data['priority'],
                    status=task_data['status'],
                    due_date=due_date
                )
        
        # Create some standalone tasks (not linked to projects)
        standalone_tasks = random.sample(task_templates, random.randint(2, 4))
        for task_data in standalone_tasks:
            due_date = None
            if random.choice([True, False]):
                due_date = timezone.now().date() + timedelta(days=random.randint(1, 20))
            
            Task.objects.create(
                title=f"Personal: {task_data['title']}",
                description=task_data['description'],
                user=user,
                priority=task_data['priority'],
                status=task_data['status'],
                due_date=due_date
            )
        
        self.stdout.write(f'Created tasks for {user.username}')

    def create_goals_for_user(self, user):
        goal_templates = [
            {
                'title': 'Complete Professional Certification',
                'description': 'Obtain industry certification to advance career',
                'category': 'career',
                'priority': 'high'
            },
            {
                'title': 'Improve Team Productivity',
                'description': 'Increase team productivity by 25% through process improvements',
                'category': 'work',
                'priority': 'medium'
            },
            {
                'title': 'Learn New Programming Language',
                'description': 'Master Python programming for data analysis projects',
                'category': 'learning',
                'priority': 'medium'
            },
            {
                'title': 'Fitness Goals',
                'description': 'Exercise regularly and maintain healthy lifestyle',
                'category': 'health',
                'priority': 'high'
            },
            {
                'title': 'Financial Planning',
                'description': 'Create and stick to monthly budget and savings plan',
                'category': 'finance',
                'priority': 'medium'
            },
            {
                'title': 'Read More Books',
                'description': 'Read at least 12 books this year on various topics',
                'category': 'personal',
                'priority': 'low'
            }
        ]
        
        # Create 3-4 goals per user
        selected_goals = random.sample(goal_templates, random.randint(3, 4))
        
        for goal_data in selected_goals:
            target_date = timezone.now().date() + timedelta(days=random.randint(60, 365))
            
            Goal.objects.create(
                title=goal_data['title'],
                description=goal_data['description'],
                user=user,
                success_criteria=f"Successfully complete {goal_data['title'].lower()}",
                target_date=target_date,
                progress_percentage=random.randint(0, 75),
                status='active'
            )
        
        self.stdout.write(f'Created goals for {user.username}')