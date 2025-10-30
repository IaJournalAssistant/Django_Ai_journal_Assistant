from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from a_planning.models import Project, Task, Goal
from datetime import datetime, timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Populate the database with sample tasks, projects, and goals'

    def handle(self, *args, **options):
        # Get or create a user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(f'Created user: {user.username}')
        else:
            self.stdout.write(f'Using existing user: {user.username}')

        # Create sample projects
        projects_data = [
            {
                'title': 'Website Redesign',
                'description': 'Complete overhaul of company website with modern design and improved UX',
                'status': 'active',
                'target_completion_date': timezone.now().date() + timedelta(days=30),
                'progress_percentage': 35
            },
            {
                'title': 'Mobile App Development',
                'description': 'Develop iOS and Android mobile application for customer engagement',
                'status': 'active',
                'target_completion_date': timezone.now().date() + timedelta(days=60),
                'progress_percentage': 15
            },
            {
                'title': 'Marketing Campaign Q4',
                'description': 'Launch comprehensive marketing campaign for Q4 product releases',
                'status': 'active',
                'target_completion_date': timezone.now().date() + timedelta(days=45),
                'progress_percentage': 25
            }
        ]

        projects = []
        for project_data in projects_data:
            project, created = Project.objects.get_or_create(
                title=project_data['title'],
                user=user,
                defaults=project_data
            )
            projects.append(project)
            if created:
                self.stdout.write(f'Created project: {project.title}')

        # Create sample tasks
        tasks_data = [
            {
                'title': 'Design wireframes',
                'description': 'Create detailed wireframes for all main pages',
                'status': 'completed',
                'priority': 'high',
                'project': projects[0],  # Website Redesign
                'due_date': timezone.now().date() - timedelta(days=5)
            },
            {
                'title': 'Develop homepage',
                'description': 'Code the new homepage with responsive design',
                'status': 'in_progress',
                'priority': 'high',
                'project': projects[0],  # Website Redesign
                'due_date': timezone.now().date() + timedelta(days=12)
            },
            {
                'title': 'Content migration',
                'description': 'Migrate existing content to new website structure',
                'status': 'pending',
                'priority': 'medium',
                'project': projects[0],  # Website Redesign
                'due_date': timezone.now().date() + timedelta(days=19)
            },
            {
                'title': 'Weekly team meeting',
                'description': 'Regular team sync and progress review',
                'status': 'pending',
                'priority': 'low',
                'due_date': timezone.now().date() + timedelta(days=1)
            },
            {
                'title': 'Market research analysis',
                'description': 'Analyze competitor landscape and market trends',
                'status': 'in_progress',
                'priority': 'medium',
                'project': projects[2],  # Marketing Campaign
                'due_date': timezone.now().date() + timedelta(days=7)
            },
            {
                'title': 'App UI mockups',
                'description': 'Create high-fidelity mockups for mobile app interface',
                'status': 'pending',
                'priority': 'high',
                'project': projects[1],  # Mobile App
                'due_date': timezone.now().date() + timedelta(days=14)
            }
        ]

        for task_data in tasks_data:
            task, created = Task.objects.get_or_create(
                title=task_data['title'],
                user=user,
                defaults=task_data
            )
            if created:
                self.stdout.write(f'Created task: {task.title}')

        # Create sample goals
        goals_data = [
            {
                'title': 'Launch New Website',
                'description': 'Successfully launch the redesigned website with improved user experience',
                'success_criteria': 'Website is live, all pages load correctly, user feedback is positive',
                'status': 'active',
                'target_date': timezone.now().date() + timedelta(days=35),
                'progress_percentage': 45
            },
            {
                'title': 'Increase Team Productivity',
                'description': 'Improve team productivity by 25% through better processes and tools',
                'success_criteria': 'Measurable 25% increase in task completion rate and reduced project delivery time',
                'status': 'active',
                'target_date': timezone.now().date() + timedelta(days=90),
                'progress_percentage': 20
            },
            {
                'title': 'Complete Mobile App MVP',
                'description': 'Deliver minimum viable product for mobile application',
                'success_criteria': 'App is published on app stores with core features working and positive user reviews',
                'status': 'active',
                'target_date': timezone.now().date() + timedelta(days=75),
                'progress_percentage': 15
            },
            {
                'title': 'Learn New Technology Stack',
                'description': 'Master React Native and GraphQL for upcoming projects',
                'success_criteria': 'Complete certification course and build a working demo application',
                'status': 'active',
                'target_date': timezone.now().date() + timedelta(days=120),
                'progress_percentage': 30
            }
        ]

        for goal_data in goals_data:
            goal, created = Goal.objects.get_or_create(
                title=goal_data['title'],
                user=user,
                defaults=goal_data
            )
            if created:
                self.stdout.write(f'Created goal: {goal.title}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated database with sample data for user: {user.username}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Created {len(projects_data)} projects, {len(tasks_data)} tasks, and {len(goals_data)} goals'
            )
        )