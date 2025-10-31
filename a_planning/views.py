"""
Views for the Task & Project Planning module
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import logging

logger = logging.getLogger(__name__)

from .models import Task, Project, Goal, TaskComment, AIInsight, AIResponseCache
from .services import ai_service
from .ai_models import (
    generate_task_insights, 
    generate_project_analysis, 
    generate_goal_action_plan, 
    generate_productivity_insights
)


@login_required
def dashboard_view(request):
    """
    Main dashboard view with overview statistics and recent items
    """
    user = request.user
    
    # Calculate statistics
    total_tasks = Task.objects.filter(user=user).count()
    completed_tasks = Task.objects.filter(user=user, status='completed').count()
    active_projects = Project.objects.filter(user=user, status='active').count()
    active_goals = Goal.objects.filter(user=user, status='active').count()
    achieved_goals = Goal.objects.filter(user=user, status='achieved').count()
    pending_insights = AIInsight.objects.filter(user=user, is_applied=False, is_dismissed=False).count()
    applied_insights = AIInsight.objects.filter(user=user, is_applied=True).count()
    
    # Calculate average project progress
    avg_progress = Project.objects.filter(user=user, status='active').aggregate(
        avg_progress=Avg('progress_percentage')
    )['avg_progress'] or 0
    
    stats = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'active_projects': active_projects,
        'active_goals': active_goals,
        'achieved_goals': achieved_goals,
        'pending_insights': pending_insights,
        'applied_insights': applied_insights,
        'avg_progress': round(avg_progress),
    }
    
    # Get recent items
    recent_tasks = Task.objects.filter(user=user).order_by('-created_at')[:5]
    active_projects_list = Project.objects.filter(user=user, status='active').order_by('-updated_at')[:3]
    active_goals_list = Goal.objects.filter(user=user, status='active').order_by('-updated_at')[:3]
    pending_insights_list = AIInsight.objects.filter(
        user=user, is_applied=False, is_dismissed=False
    ).order_by('-created_at')[:3]
    
    context = {
        'active_tab': 'dashboard',
        'stats': stats,
        'recent_tasks': recent_tasks,
        'active_projects': active_projects_list,
        'active_goals': active_goals_list,
        'pending_insights': pending_insights_list,
    }
    
    return render(request, 'a_planning/dashboard.html', context)


@login_required
def task_list_view(request):
    """
    Task list view with filtering and search
    """
    tasks = Task.objects.filter(user=request.user)
    
    # Apply filters
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    project_filter = request.GET.get('project')
    search_query = request.GET.get('search')
    
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    
    if project_filter:
        if project_filter == 'none':
            tasks = tasks.filter(project__isnull=True)
        else:
            tasks = tasks.filter(project_id=project_filter)
    
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    tasks = tasks.order_by('-created_at')
    
    # Get filter options
    projects = Project.objects.filter(user=request.user, status='active')
    
    context = {
        'active_tab': 'tasks',
        'tasks': tasks,
        'projects': projects,
        'current_filters': {
            'status': status_filter,
            'priority': priority_filter,
            'project': project_filter,
            'search': search_query,
        }
    }
    
    return render(request, 'a_planning/task_list.html', context)


@login_required
def task_create_view(request):
    """
    Create a new task
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        priority = request.POST.get('priority', 'medium')
        project_id = request.POST.get('project')
        due_date = request.POST.get('due_date')
        
        if not title:
            messages.error(request, 'Task title is required.')
            return redirect('planning:task-create')
        
        task = Task.objects.create(
            title=title,
            description=description,
            priority=priority,
            user=request.user,
            due_date=due_date if due_date else None
        )
        
        if project_id:
            try:
                project = Project.objects.get(id=project_id, user=request.user)
                task.project = project
                task.save()
                project.update_progress()
            except Project.DoesNotExist:
                pass
        
        messages.success(request, f'Task "{title}" created successfully!')
        return redirect('planning:task-list')
    
    projects = Project.objects.filter(user=request.user, status='active')
    
    context = {
        'active_tab': 'tasks',
        'projects': projects,
    }
    
    return render(request, 'a_planning/task_form.html', context)


@login_required
def task_detail_view(request, task_id):
    """
    Task detail view with comments and actions
    """
    task = get_object_or_404(Task, id=task_id, user=request.user)
    comments = task.comments.all().order_by('created_at')
    
    context = {
        'active_tab': 'tasks',
        'task': task,
        'comments': comments,
    }
    
    return render(request, 'a_planning/task_detail.html', context)


@login_required
def task_edit_view(request, task_id):
    """
    Edit an existing task
    """
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        priority = request.POST.get('priority', 'medium')
        project_id = request.POST.get('project')
        due_date = request.POST.get('due_date')
        
        if not title:
            messages.error(request, 'Task title is required.')
            return redirect('planning:task-edit', task_id=task.id)
        
        task.title = title
        task.description = description
        task.priority = priority
        task.due_date = due_date if due_date else None
        
        if project_id:
            try:
                project = Project.objects.get(id=project_id, user=request.user)
                task.project = project
            except Project.DoesNotExist:
                task.project = None
        else:
            task.project = None
        
        task.save()
        
        # Update project progress if task is in a project
        if task.project:
            task.project.update_progress()
        
        messages.success(request, f'Task "{title}" updated successfully!')
        return redirect('planning:task-detail', task_id=task.id)
    
    projects = Project.objects.filter(user=request.user, status='active')
    
    context = {
        'active_tab': 'tasks',
        'task': task,
        'projects': projects,
        'is_edit': True,
    }
    
    return render(request, 'a_planning/task_form.html', context)


@login_required
def task_delete_view(request, task_id):
    """
    Delete a task
    """
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        task_title = task.title
        project = task.project
        task.delete()
        
        # Update project progress if task was in a project
        if project:
            project.update_progress()
        
        messages.success(request, f'Task "{task_title}" deleted successfully!')
        return redirect('planning:task-list')
    
    context = {
        'active_tab': 'tasks',
        'task': task,
    }
    
    return render(request, 'a_planning/task_confirm_delete.html', context)


@login_required
def task_add_comment_view(request, task_id):
    """
    Add a comment to a task
    """
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        
        if content:
            TaskComment.objects.create(
                task=task,
                user=request.user,
                content=content
            )
            messages.success(request, 'Comment added successfully!')
        else:
            messages.error(request, 'Comment content is required.')
    
    return redirect('planning:task-detail', task_id=task.id)


@login_required
def project_list_view(request):
    """
    Project list view with filtering
    """
    projects = Project.objects.filter(user=request.user)
    
    # Apply filters
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')
    
    if status_filter:
        projects = projects.filter(status=status_filter)
    
    if search_query:
        projects = projects.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    projects = projects.order_by('-created_at')
    
    context = {
        'active_tab': 'projects',
        'projects': projects,
        'current_filters': {
            'status': status_filter,
            'search': search_query,
        }
    }
    
    return render(request, 'a_planning/project_list.html', context)


@login_required
def project_create_view(request):
    """
    Create a new project
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        start_date = request.POST.get('start_date')
        target_completion_date = request.POST.get('target_completion_date')
        
        if not title:
            messages.error(request, 'Project title is required.')
            return redirect('planning:project-create')
        
        project = Project.objects.create(
            title=title,
            description=description,
            user=request.user,
            start_date=start_date if start_date else None,
            target_completion_date=target_completion_date if target_completion_date else None
        )
        
        messages.success(request, f'Project "{title}" created successfully!')
        return redirect('planning:project-list')
    
    context = {
        'active_tab': 'projects',
    }
    
    return render(request, 'a_planning/project_form.html', context)


@login_required
def project_detail_view(request, project_id):
    """
    Project detail view with tasks
    """
    project = get_object_or_404(Project, id=project_id, user=request.user)
    tasks = project.tasks.all().order_by('-created_at')
    
    context = {
        'active_tab': 'projects',
        'project': project,
        'tasks': tasks,
    }
    
    return render(request, 'a_planning/project_detail.html', context)


@login_required
def project_edit_view(request, project_id):
    """
    Edit an existing project
    """
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        start_date = request.POST.get('start_date')
        target_completion_date = request.POST.get('target_completion_date')
        
        if not title:
            messages.error(request, 'Project title is required.')
            return redirect('planning:project-edit', project_id=project.id)
        
        project.title = title
        project.description = description
        project.start_date = start_date if start_date else None
        project.target_completion_date = target_completion_date if target_completion_date else None
        project.save()
        
        messages.success(request, f'Project "{title}" updated successfully!')
        return redirect('planning:project-detail', project_id=project.id)
    
    context = {
        'active_tab': 'projects',
        'project': project,
        'is_edit': True,
    }
    
    return render(request, 'a_planning/project_form.html', context)


@login_required
@require_http_methods(["POST"])
def project_mark_completed_view(request, project_id):
    """
    Mark a project as completed
    """
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    try:
        project.mark_completed()
        return JsonResponse({
            'success': True,
            'status': project.status,
            'completed_at': project.completed_at.isoformat() if project.completed_at else None
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def project_pause_view(request, project_id):
    """
    Put a project on hold
    """
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    try:
        project.status = 'on_hold'
        project.save()
        return JsonResponse({
            'success': True,
            'status': project.status
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def project_resume_view(request, project_id):
    """
    Resume a project that's on hold
    """
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    try:
        project.status = 'active'
        project.save()
        return JsonResponse({
            'success': True,
            'status': project.status
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def project_delete_view(request, project_id):
    """
    Delete a project
    """
    project = get_object_or_404(Project, id=project_id, user=request.user)
    
    try:
        project_title = project.title
        project.delete()
        return JsonResponse({
            'success': True,
            'message': f'Project "{project_title}" deleted successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def goal_list_view(request):
    """
    Goal list view with filtering
    """
    goals = Goal.objects.filter(user=request.user)
    
    # Apply filters
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')
    
    if status_filter:
        goals = goals.filter(status=status_filter)
    
    if search_query:
        goals = goals.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(success_criteria__icontains=search_query)
        )
    
    goals = goals.order_by('-created_at')
    
    context = {
        'active_tab': 'goals',
        'goals': goals,
        'current_filters': {
            'status': status_filter,
            'search': search_query,
        }
    }
    
    return render(request, 'a_planning/goal_list.html', context)


@login_required
def goal_create_view(request):
    """
    Create a new goal
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        success_criteria = request.POST.get('success_criteria')
        target_date = request.POST.get('target_date')
        
        if not title or not success_criteria or not target_date:
            messages.error(request, 'Title, success criteria, and target date are required.')
            return redirect('planning:goal-create')
        
        goal = Goal.objects.create(
            title=title,
            description=description,
            success_criteria=success_criteria,
            target_date=target_date,
            user=request.user
        )
        
        messages.success(request, f'Goal "{title}" created successfully!')
        return redirect('planning:goal-list')
    
    context = {
        'active_tab': 'goals',
    }
    
    return render(request, 'a_planning/goal_form.html', context)


@login_required
def goal_detail_view(request, goal_id):
    """
    Goal detail view with progress tracking
    """
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    
    context = {
        'active_tab': 'goals',
        'goal': goal,
    }
    
    return render(request, 'a_planning/goal_detail.html', context)


@login_required
def goal_edit_view(request, goal_id):
    """
    Edit an existing goal
    """
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        success_criteria = request.POST.get('success_criteria')
        target_date = request.POST.get('target_date')
        
        if not title or not success_criteria or not target_date:
            messages.error(request, 'Title, success criteria, and target date are required.')
            return redirect('planning:goal-edit', goal_id=goal.id)
        
        goal.title = title
        goal.description = description
        goal.success_criteria = success_criteria
        goal.target_date = target_date
        goal.save()
        
        messages.success(request, f'Goal "{title}" updated successfully!')
        return redirect('planning:goal-detail', goal_id=goal.id)
    
    context = {
        'active_tab': 'goals',
        'goal': goal,
        'is_edit': True,
    }
    
    return render(request, 'a_planning/goal_form.html', context)


@login_required
@require_http_methods(["POST"])
def goal_mark_achieved_view(request, goal_id):
    """
    Mark a goal as achieved
    """
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    
    try:
        goal.mark_achieved()
        return JsonResponse({
            'success': True,
            'status': goal.status,
            'achieved_at': goal.achieved_at.isoformat() if goal.achieved_at else None
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def goal_pause_view(request, goal_id):
    """
    Pause a goal
    """
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    
    try:
        goal.status = 'paused'
        goal.save()
        return JsonResponse({
            'success': True,
            'status': goal.status
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def goal_resume_view(request, goal_id):
    """
    Resume a paused goal
    """
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    
    try:
        goal.status = 'active'
        goal.save()
        return JsonResponse({
            'success': True,
            'status': goal.status
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_http_methods(["POST"])
def goal_delete_view(request, goal_id):
    """
    Delete a goal
    """
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    
    try:
        goal_title = goal.title
        goal.delete()
        return JsonResponse({
            'success': True,
            'message': f'Goal "{goal_title}" deleted successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# HTMX Views for dynamic updates
@login_required
@require_http_methods(["POST"])
def task_toggle_status(request, task_id):
    """
    Toggle task status via HTMX
    """
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if task.status == 'completed':
        task.status = 'pending'
    elif task.status == 'pending':
        task.status = 'in_progress'
    else:  # in_progress
        task.mark_completed()
    
    task.save()
    
    # Update project progress if task is in a project
    if task.project:
        task.project.update_progress()
    
    return JsonResponse({
        'status': task.status,
        'status_display': task.get_status_display(),
        'completed_at': task.completed_at.isoformat() if task.completed_at else None
    })


@login_required
@require_http_methods(["POST"])
def project_update_progress(request, project_id):
    """
    Update project progress via HTMX
    """
    project = get_object_or_404(Project, id=project_id, user=request.user)
    project.update_progress()
    
    return JsonResponse({
        'progress_percentage': project.progress_percentage,
        'task_counts': project.get_task_counts()
    })


@login_required
@require_http_methods(["POST"])
def goal_update_progress(request, goal_id):
    """
    Update goal progress via HTMX
    """
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    percentage = request.POST.get('percentage')
    
    if percentage:
        try:
            percentage = int(percentage)
            if 0 <= percentage <= 100:
                goal.update_progress(percentage)
                return JsonResponse({
                    'progress_percentage': goal.progress_percentage,
                    'status': goal.status,
                    'achieved_at': goal.achieved_at.isoformat() if goal.achieved_at else None
                })
        except (ValueError, TypeError):
            pass
    
    return JsonResponse({'error': 'Invalid percentage'}, status=400)


# AI-Powered Views using n8n integration
@login_required
def ai_task_summary_view(request):
    """
    Generate AI summary of user's tasks using n8n webhook
    """
    tasks = Task.objects.filter(user=request.user).values(
        'title', 'description', 'status', 'priority', 'due_date', 'project__title'
    )
    
    # Convert QuerySet to list for JSON serialization
    task_list = []
    for task in tasks:
        task_data = {
            'title': task['title'],
            'description': task['description'] or '',
            'status': task['status'],
            'priority': task['priority'],
            'due_date': task['due_date'].isoformat() if task['due_date'] else None,
            'project_title': task['project__title']
        }
        task_list.append(task_data)
    
    # Try n8n first, then fallback to local AI, then cache
    summary = ai_service.summarize_tasks(task_list)
    
    if summary:
        # Save the successful n8n response to cache
        AIResponseCache.save_response(
            user=request.user,
            response_type='task_summary',
            response_content=summary
        )
        
        return JsonResponse({
            'success': True,
            'summary': summary,
            'task_count': len(task_list),
            'source': 'n8n'
        })
    else:
        # Try local AI model as fallback
        try:
            local_summary = generate_task_insights(task_list)
            if local_summary:
                # Save local AI response to cache
                AIResponseCache.save_response(
                    user=request.user,
                    response_type='task_summary',
                    response_content=local_summary
                )
                
                return JsonResponse({
                    'success': True,
                    'summary': local_summary,
                    'task_count': len(task_list),
                    'source': 'local_ai'
                })
        except Exception as e:
            logger.error(f"Local AI failed: {e}")
        
        # Finally, try cached response
        cached_response = AIResponseCache.get_cached_response(
            user=request.user,
            response_type='task_summary'
        )
        
        if cached_response:
            return JsonResponse({
                'success': True,
                'summary': cached_response.response_content,
                'task_count': len(task_list),
                'is_cached': True,
                'cached_date': cached_response.updated_at.isoformat()
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'AI services unavailable. Please try again later.'
            })


@login_required
def ai_project_analysis_view(request, project_id):
    """
    Generate AI analysis of project progress using n8n webhook
    """
    project = get_object_or_404(Project, id=project_id, user=request.user)
    tasks = project.tasks.all().values(
        'title', 'status', 'priority', 'due_date'
    )
    
    # Prepare project data
    project_data = {
        'title': project.title,
        'description': project.description,
        'progress_percentage': project.progress_percentage,
        'status': project.status,
        'target_completion_date': project.target_completion_date.isoformat() if project.target_completion_date else None
    }
    
    # Convert tasks to list
    task_list = []
    for task in tasks:
        task_data = {
            'title': task['title'],
            'status': task['status'],
            'priority': task['priority'],
            'due_date': task['due_date'].isoformat() if task['due_date'] else None
        }
        task_list.append(task_data)
    
    # Try n8n first, then fallback to local AI, then cache
    analysis = ai_service.analyze_project_progress(project_data, task_list)
    
    if analysis:
        # Save the successful n8n response to cache
        AIResponseCache.save_response(
            user=request.user,
            response_type='project_analysis',
            response_content=analysis,
            content_object=project
        )
        
        return JsonResponse({
            'success': True,
            'analysis': analysis,
            'project_title': project.title,
            'source': 'n8n'
        })
    else:
        # Try local AI model as fallback
        try:
            local_analysis = generate_project_analysis(project_data, task_list)
            if local_analysis:
                # Save local AI response to cache
                AIResponseCache.save_response(
                    user=request.user,
                    response_type='project_analysis',
                    response_content=local_analysis,
                    content_object=project
                )
                
                return JsonResponse({
                    'success': True,
                    'analysis': local_analysis,
                    'project_title': project.title,
                    'source': 'local_ai'
                })
        except Exception as e:
            logger.error(f"Local AI failed: {e}")
        
        # Finally, try cached response
        cached_response = AIResponseCache.get_cached_response(
            user=request.user,
            response_type='project_analysis',
            content_object=project
        )
        
        if cached_response:
            return JsonResponse({
                'success': True,
                'analysis': cached_response.response_content,
                'project_title': project.title,
                'is_cached': True,
                'cached_date': cached_response.updated_at.isoformat()
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'AI services unavailable. Please try again later.'
            })


@login_required
def ai_task_breakdown_view(request):
    """
    Get AI suggestions for breaking down a complex task
    """
    if request.method == 'POST':
        task_title = request.POST.get('title', '')
        task_description = request.POST.get('description', '')
        
        if not task_title:
            return JsonResponse({
                'success': False,
                'error': 'Task title is required'
            })
        
        # Get AI suggestions from n8n
        suggestions = ai_service.suggest_task_breakdown(task_title, task_description)
        
        if suggestions:
            return JsonResponse({
                'success': True,
                'suggestions': suggestions,
                'original_title': task_title
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to generate task breakdown. Please check your n8n workflow.'
            })
    
    return JsonResponse({'success': False, 'error': 'POST method required'})


@login_required
def ai_goal_action_plan_view(request, goal_id):
    """
    Generate AI action plan for achieving a goal
    """
    goal = get_object_or_404(Goal, id=goal_id, user=request.user)
    
    # Prepare goal data
    goal_data = {
        'title': goal.title,
        'description': goal.description,
        'success_criteria': goal.success_criteria,
        'target_date': goal.target_date.isoformat() if goal.target_date else None,
        'progress_percentage': goal.progress_percentage
    }
    
    # Get AI action plan from n8n
    action_plan = ai_service.generate_goal_action_plan(goal_data)
    
    if action_plan:
        # Save the successful response to cache
        AIResponseCache.save_response(
            user=request.user,
            response_type='goal_action_plan',
            response_content=action_plan,
            content_object=goal
        )
        
        return JsonResponse({
            'success': True,
            'action_plan': action_plan,
            'goal_title': goal.title
        })
    else:
        # Try to get cached response when AI fails
        cached_response = AIResponseCache.get_cached_response(
            user=request.user,
            response_type='goal_action_plan',
            content_object=goal
        )
        
        if cached_response:
            return JsonResponse({
                'success': True,
                'action_plan': cached_response.response_content,
                'goal_title': goal.title,
                'is_cached': True,
                'cached_date': cached_response.updated_at.isoformat()
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to generate action plan. Please check your n8n workflow.'
            })


@login_required
def ai_productivity_insights_view(request):
    """
    Generate AI insights about user's productivity patterns
    """
    # Gather user productivity data
    total_tasks = Task.objects.filter(user=request.user).count()
    completed_tasks = Task.objects.filter(user=request.user, status='completed').count()
    overdue_tasks = Task.objects.filter(
        user=request.user, 
        due_date__lt=timezone.now(),
        status__in=['pending', 'in_progress']
    ).count()
    
    active_projects = Project.objects.filter(user=request.user, status='active').count()
    completed_projects = Project.objects.filter(user=request.user, status='completed').count()
    
    active_goals = Goal.objects.filter(user=request.user, status='active').count()
    achieved_goals = Goal.objects.filter(user=request.user, status='achieved').count()
    
    # Calculate completion rates
    task_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    project_completion_rate = (completed_projects / (active_projects + completed_projects) * 100) if (active_projects + completed_projects) > 0 else 0
    goal_achievement_rate = (achieved_goals / (active_goals + achieved_goals) * 100) if (active_goals + achieved_goals) > 0 else 0
    
    user_data = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'task_completion_rate': round(task_completion_rate, 1),
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'project_completion_rate': round(project_completion_rate, 1),
        'active_goals': active_goals,
        'achieved_goals': achieved_goals,
        'goal_achievement_rate': round(goal_achievement_rate, 1)
    }
    
    # Get AI insights from n8n
    insights = ai_service.analyze_productivity_patterns(user_data)
    
    if insights:
        # Save the successful response to cache
        AIResponseCache.save_response(
            user=request.user,
            response_type='productivity_insights',
            response_content=insights
        )
        
        return JsonResponse({
            'success': True,
            'insights': insights,
            'productivity_data': user_data
        })
    else:
        # Try to get cached response when AI fails
        cached_response = AIResponseCache.get_cached_response(
            user=request.user,
            response_type='productivity_insights'
        )
        
        if cached_response:
            return JsonResponse({
                'success': True,
                'insights': cached_response.response_content,
                'productivity_data': user_data,
                'is_cached': True,
                'cached_date': cached_response.updated_at.isoformat()
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to generate productivity insights. Please check your n8n workflow.'
            })