from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Task, Project, Goal, TaskComment, AIInsight


class TaskCommentInline(admin.TabularInline):
    """Inline admin for task comments"""
    model = TaskComment
    extra = 1
    fields = ('user', 'content', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin interface for Task model"""
    list_display = (
        'title', 
        'user', 
        'project_link', 
        'status_badge', 
        'priority_badge', 
        'due_date', 
        'ai_suggested',
        'created_at'
    )
    list_filter = (
        'status', 
        'priority', 
        'ai_suggested', 
        'created_at', 
        'due_date',
        'project'
    )
    search_fields = ('title', 'description', 'user__username', 'project__title')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'user', 'project')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'ai_suggested')
        }),
        ('Dates & Duration', {
            'fields': ('due_date', 'estimated_duration', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
            'description': 'Automatically managed timestamps'
        })
    )
    
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    inlines = [TaskCommentInline]
    
    actions = ['mark_completed', 'mark_in_progress', 'mark_pending']
    
    def project_link(self, obj):
        """Display project as a clickable link"""
        if obj.project:
            url = reverse('admin:a_planning_project_change', args=[obj.project.pk])
            return format_html('<a href="{}">{}</a>', url, obj.project.title)
        return '-'
    project_link.short_description = 'Project'
    
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': '#ffc107',
            'in_progress': '#007bff', 
            'completed': '#28a745',
            'cancelled': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def priority_badge(self, obj):
        """Display priority with color coding"""
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14', 
            'urgent': '#dc3545'
        }
        color = colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def mark_completed(self, request, queryset):
        """Bulk action to mark tasks as completed"""
        updated = 0
        for task in queryset:
            task.mark_completed()
            updated += 1
        self.message_user(request, f'{updated} tasks marked as completed.')
    mark_completed.short_description = 'Mark selected tasks as completed'
    
    def mark_in_progress(self, request, queryset):
        """Bulk action to mark tasks as in progress"""
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'{updated} tasks marked as in progress.')
    mark_in_progress.short_description = 'Mark selected tasks as in progress'
    
    def mark_pending(self, request, queryset):
        """Bulk action to mark tasks as pending"""
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} tasks marked as pending.')
    mark_pending.short_description = 'Mark selected tasks as pending'


class TaskInline(admin.TabularInline):
    """Inline admin for tasks within projects"""
    model = Task
    extra = 1
    fields = ('title', 'status', 'priority', 'due_date', 'ai_suggested')
    classes = ('collapse',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin interface for Project model"""
    list_display = (
        'title',
        'user', 
        'status_badge',
        'progress_bar',
        'task_count',
        'start_date',
        'target_completion_date',
        'created_at'
    )
    list_filter = (
        'status',
        'created_at',
        'start_date',
        'target_completion_date'
    )
    search_fields = ('title', 'description', 'user__username')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'user')
        }),
        ('Status & Progress', {
            'fields': ('status', 'progress_percentage')
        }),
        ('Timeline', {
            'fields': ('start_date', 'target_completion_date', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'progress_percentage')
    inlines = [TaskInline]
    
    actions = ['update_progress', 'mark_completed']
    
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'active': '#007bff',
            'completed': '#28a745',
            'on_hold': '#ffc107',
            'cancelled': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def progress_bar(self, obj):
        """Display progress as a visual bar"""
        percentage = obj.progress_percentage
        color = '#28a745' if percentage == 100 else '#007bff' if percentage >= 50 else '#ffc107'
        return format_html(
            '<div style="width: 100px; background-color: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; '
            'text-align: center; line-height: 20px; color: white; font-size: 12px;">{}</div></div>',
            percentage, color, f'{percentage}%'
        )
    progress_bar.short_description = 'Progress'
    
    def task_count(self, obj):
        """Display number of tasks in project"""
        counts = obj.get_task_counts()
        return format_html(
            '<span title="Total: {total}, Completed: {completed}, In Progress: {in_progress}, Pending: {pending}">'
            '{total} tasks</span>',
            **counts
        )
    task_count.short_description = 'Tasks'
    
    def update_progress(self, request, queryset):
        """Bulk action to recalculate project progress"""
        updated = 0
        for project in queryset:
            project.update_progress()
            updated += 1
        self.message_user(request, f'Progress updated for {updated} projects.')
    update_progress.short_description = 'Recalculate progress for selected projects'
    
    def mark_completed(self, request, queryset):
        """Bulk action to mark projects as completed"""
        updated = 0
        for project in queryset:
            project.mark_completed()
            updated += 1
        self.message_user(request, f'{updated} projects marked as completed.')
    mark_completed.short_description = 'Mark selected projects as completed'

@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    """Admin interface for Goal model"""
    list_display = (
        'title',
        'user',
        'status_badge',
        'progress_bar',
        'target_date',
        'days_remaining',
        'created_at'
    )
    list_filter = (
        'status',
        'created_at',
        'target_date'
    )
    search_fields = ('title', 'description', 'success_criteria', 'user__username')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'user')
        }),
        ('Goal Details', {
            'fields': ('success_criteria', 'target_date')
        }),
        ('Progress Tracking', {
            'fields': ('status', 'progress_percentage', 'achieved_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at', 'achieved_at')
    
    actions = ['mark_achieved', 'update_progress_50', 'update_progress_75']
    
    def status_badge(self, obj):
        """Display status with color coding"""
        colors = {
            'active': '#007bff',
            'achieved': '#28a745',
            'paused': '#ffc107',
            'cancelled': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def progress_bar(self, obj):
        """Display progress as a visual bar"""
        percentage = obj.progress_percentage
        color = '#28a745' if percentage == 100 else '#007bff' if percentage >= 50 else '#ffc107'
        return format_html(
            '<div style="width: 100px; background-color: #e9ecef; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; '
            'text-align: center; line-height: 20px; color: white; font-size: 12px;">{}</div></div>',
            percentage, color, f'{percentage}%'
        )
    progress_bar.short_description = 'Progress'
    
    def days_remaining(self, obj):
        """Display days until target date"""
        days = obj.days_until_target()
        if days is None:
            return '-'
        elif days < 0:
            return format_html('<span style="color: #dc3545;">Overdue by {} days</span>', abs(days))
        elif days == 0:
            return format_html('<span style="color: #ffc107;">Due today</span>')
        else:
            return format_html('<span style="color: #28a745;">{} days left</span>', days)
    days_remaining.short_description = 'Time Remaining'
    
    def mark_achieved(self, request, queryset):
        """Bulk action to mark goals as achieved"""
        updated = 0
        for goal in queryset:
            goal.mark_achieved()
            updated += 1
        self.message_user(request, f'{updated} goals marked as achieved.')
    mark_achieved.short_description = 'Mark selected goals as achieved'
    
    def update_progress_50(self, request, queryset):
        """Bulk action to set progress to 50%"""
        updated = 0
        for goal in queryset:
            goal.update_progress(50)
            updated += 1
        self.message_user(request, f'Progress set to 50% for {updated} goals.')
    update_progress_50.short_description = 'Set progress to 50%'
    
    def update_progress_75(self, request, queryset):
        """Bulk action to set progress to 75%"""
        updated = 0
        for goal in queryset:
            goal.update_progress(75)
            updated += 1
        self.message_user(request, f'Progress set to 75% for {updated} goals.')
    update_progress_75.short_description = 'Set progress to 75%'


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    """Admin interface for TaskComment model"""
    list_display = ('task_link', 'user', 'content_preview', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('content', 'task__title', 'user__username')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fields = ('task', 'user', 'content', 'created_at')
    readonly_fields = ('created_at',)
    
    def task_link(self, obj):
        """Display task as a clickable link"""
        url = reverse('admin:a_planning_task_change', args=[obj.task.pk])
        return format_html('<a href="{}">{}</a>', url, obj.task.title)
    task_link.short_description = 'Task'
    
    def content_preview(self, obj):
        """Display truncated content"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    """Admin interface for AIInsight model"""
    list_display = (
        'user',
        'insight_type_badge',
        'content_object_link',
        'content_preview',
        'is_applied',
        'is_dismissed',
        'created_at'
    )
    list_filter = (
        'insight_type',
        'is_applied',
        'is_dismissed',
        'created_at',
        'content_type'
    )
    search_fields = ('content', 'user__username')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'insight_type', 'content')
        }),
        ('Target Object', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_applied', 'is_dismissed', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at',)
    
    actions = ['mark_applied', 'mark_dismissed']
    
    def insight_type_badge(self, obj):
        """Display insight type with color coding"""
        colors = {
            'task_suggestion': '#007bff',
            'project_planning': '#28a745',
            'goal_analysis': '#ffc107',
            'productivity_tip': '#17a2b8',
            'priority_recommendation': '#fd7e14',
            'timeline_suggestion': '#6f42c1'
        }
        color = colors.get(obj.insight_type, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_insight_type_display()
        )
    insight_type_badge.short_description = 'Type'
    
    def content_object_link(self, obj):
        """Display content object as a clickable link"""
        if obj.content_object:
            if hasattr(obj.content_object, '_meta'):
                model_name = obj.content_object._meta.model_name
                app_label = obj.content_object._meta.app_label
                try:
                    url = reverse(f'admin:{app_label}_{model_name}_change', args=[obj.object_id])
                    return format_html('<a href="{}">{}</a>', url, str(obj.content_object))
                except:
                    return str(obj.content_object)
        return '-'
    content_object_link.short_description = 'Related Object'
    
    def content_preview(self, obj):
        """Display truncated content"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
    
    def mark_applied(self, request, queryset):
        """Bulk action to mark insights as applied"""
        updated = queryset.update(is_applied=True)
        self.message_user(request, f'{updated} insights marked as applied.')
    mark_applied.short_description = 'Mark selected insights as applied'
    
    def mark_dismissed(self, request, queryset):
        """Bulk action to mark insights as dismissed"""
        updated = queryset.update(is_dismissed=True)
        self.message_user(request, f'{updated} insights marked as dismissed.')
    mark_dismissed.short_description = 'Mark selected insights as dismissed'


# Customize admin site header and title
admin.site.site_header = 'Task & Project Planning Administration'
admin.site.site_title = 'Planning Admin'
admin.site.index_title = 'Welcome to Task & Project Planning Administration'