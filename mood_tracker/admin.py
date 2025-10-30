from django.contrib import admin
from .models import MoodEntry, Habit, HabitLog, AIInsight


@admin.register(MoodEntry)
class MoodEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'mood_level', 'mood_label', 'date', 'created_at']
    list_filter = ['mood_level', 'mood_label', 'date', 'created_at']
    search_fields = ['user__username', 'user__email', 'notes']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Mood Information', {
            'fields': ('user', 'mood_level', 'mood_label', 'date')
        }),
        ('Additional Details', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'user__username', 'user__email', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Habit Information', {
            'fields': ('user', 'name', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(HabitLog)
class HabitLogAdmin(admin.ModelAdmin):
    list_display = ['habit', 'date', 'completed', 'created_at']
    list_filter = ['completed', 'date', 'created_at', 'habit__name']
    search_fields = ['habit__name', 'habit__user__username', 'notes']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Log Information', {
            'fields': ('habit', 'date', 'completed')
        }),
        ('Additional Details', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('habit', 'habit__user')


@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = ['user', 'insight_type', 'data_period_start', 'data_period_end', 'generated_at', 'is_archived']
    list_filter = ['insight_type', 'is_archived', 'generated_at', 'data_period_start']
    search_fields = ['user__username', 'user__email', 'content']
    date_hierarchy = 'generated_at'
    ordering = ['-generated_at']
    readonly_fields = ['generated_at', 'data_period_days']
    
    fieldsets = (
        ('Insight Information', {
            'fields': ('user', 'insight_type', 'data_period_start', 'data_period_end', 'data_period_days')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Status', {
            'fields': ('is_archived',)
        }),
        ('Timestamps', {
            'fields': ('generated_at',),
            'classes': ('collapse',)
        }),
    )
    
    def data_period_days(self, obj):
        return obj.data_period_days
    data_period_days.short_description = 'Period Length (days)'
