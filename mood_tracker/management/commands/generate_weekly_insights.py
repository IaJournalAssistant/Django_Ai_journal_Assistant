"""
Management command to generate weekly insights for all users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta

from mood_tracker.ai_engine import AIAnalysisEngine
from mood_tracker.models import MoodEntry, Habit, AIInsight


class Command(BaseCommand):
    help = 'Generate weekly insights for all users with sufficient data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Generate insights for a specific user ID only',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force generation even if recent insights exist',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually generating insights',
        )

    def handle(self, *args, **options):
        ai_engine = AIAnalysisEngine()
        
        # Get users to process
        if options['user_id']:
            users = User.objects.filter(id=options['user_id'])
            if not users.exists():
                self.stdout.write(
                    self.style.ERROR(f'User with ID {options["user_id"]} not found')
                )
                return
        else:
            # Get all users who have mood or habit data
            users_with_mood_data = User.objects.filter(mood_entries__isnull=False).distinct()
            users_with_habit_data = User.objects.filter(habits__isnull=False).distinct()
            users = (users_with_mood_data | users_with_habit_data).distinct()

        self.stdout.write(f'Processing {users.count()} users...')

        generated_count = 0
        skipped_count = 0
        error_count = 0

        for user in users:
            try:
                # Check if user has sufficient data
                if not self._has_sufficient_data(user):
                    self.stdout.write(
                        self.style.WARNING(f'Skipping {user.username}: insufficient data')
                    )
                    skipped_count += 1
                    continue

                # Check if recent insights already exist (unless forced)
                if not options['force'] and self._has_recent_insights(user):
                    self.stdout.write(
                        self.style.WARNING(f'Skipping {user.username}: recent insights exist')
                    )
                    skipped_count += 1
                    continue

                if options['dry_run']:
                    self.stdout.write(
                        self.style.SUCCESS(f'Would generate insights for {user.username}')
                    )
                    continue

                # Generate insights
                self.stdout.write(f'Generating insights for {user.username}...')
                
                insights_data = ai_engine.generate_weekly_insights(user)
                
                if 'error' in insights_data:
                    self.stdout.write(
                        self.style.ERROR(f'Error generating insights for {user.username}: {insights_data["message"]}')
                    )
                    error_count += 1
                    continue

                # Save to database
                ai_insight = ai_engine.save_insights_to_database(
                    user=user,
                    insights=insights_data,
                    insight_type='weekly'
                )

                if ai_insight:
                    self.stdout.write(
                        self.style.SUCCESS(f'Generated insights for {user.username}')
                    )
                    generated_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to save insights for {user.username}')
                    )
                    error_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing {user.username}: {str(e)}')
                )
                error_count += 1

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Summary:')
        self.stdout.write(f'  Generated: {generated_count}')
        self.stdout.write(f'  Skipped: {skipped_count}')
        self.stdout.write(f'  Errors: {error_count}')
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('This was a dry run - no insights were actually generated'))

    def _has_sufficient_data(self, user: User) -> bool:
        """Check if user has sufficient data for meaningful insights"""
        # Check for mood data in the last 7 days
        week_ago = date.today() - timedelta(days=6)
        mood_count = MoodEntry.objects.filter(
            user=user,
            date__gte=week_ago
        ).count()

        # Check for active habits
        active_habits = Habit.objects.filter(user=user, is_active=True).count()

        # Need at least 3 mood entries in the last week OR active habits
        return mood_count >= 3 or active_habits > 0

    def _has_recent_insights(self, user: User) -> bool:
        """Check if user has insights generated in the last 24 hours"""
        yesterday = timezone.now() - timedelta(hours=24)
        return AIInsight.objects.filter(
            user=user,
            insight_type='weekly',
            generated_at__gte=yesterday
        ).exists()