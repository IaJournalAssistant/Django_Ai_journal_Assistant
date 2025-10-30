from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from allauth.account.utils import send_email_confirmation
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth.views import redirect_to_login
from django.contrib import messages
from django.http import JsonResponse
from .forms import *
from .ai_service import generate_user_bio

def profile_view(request, username=None):
    if username:
        profile = get_object_or_404(User, username=username).profile
    else:
        try:
            profile = request.user.profile
        except:
            return redirect_to_login(request.get_full_path())
    
    # Split interests into a list for template
    interests_list = []
    if profile.interests:
        interests_list = [interest.strip() for interest in profile.interests.split(',') if interest.strip()]
    
    return render(request, 'a_users/profile.html', {
        'profile': profile,
        'interests_list': interests_list
    })


@login_required
def profile_edit_view(request):
    form = ProfileForm(instance=request.user.profile)  
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
        
    if request.path == reverse('profile-onboarding'):
        onboarding = True
    else:
        onboarding = False
      
    return render(request, 'a_users/profile_edit.html', { 'form':form, 'onboarding':onboarding })


@login_required
def profile_settings_view(request):
    return render(request, 'a_users/profile_settings.html')


@login_required
def profile_emailchange(request):
    
    if request.htmx:
        form = EmailForm(instance=request.user)
        return render(request, 'partials/email_form.html', {'form':form})
    
    if request.method == 'POST':
        form = EmailForm(request.POST, instance=request.user)

        if form.is_valid():
            
            # Check if the email already exists
            email = form.cleaned_data['email']
            if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                messages.warning(request, f'{email} is already in use.')
                return redirect('profile-settings')
            
            form.save() 
            
            # Then Signal updates emailaddress and set verified to False
            
            # Then send confirmation email 
            # send_email_confirmation() will be deprecated soon!
            send_email_confirmation(request, request.user)
            
            return redirect('profile-settings')
        else:
            messages.warning(request, 'Email not valid or already in use')
            return redirect('profile-settings')
        
    return redirect('profile-settings')


@login_required
def profile_usernamechange(request):
    if request.htmx:
        form = UsernameForm(instance=request.user)
        return render(request, 'partials/username_form.html', {'form':form})
    
    if request.method == 'POST':
        form = UsernameForm(request.POST, instance=request.user)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Username updated successfully.')
            return redirect('profile-settings')
        else:
            messages.warning(request, 'Username not valid or already in use')
            return redirect('profile-settings')
    
    return redirect('profile-settings')    


@login_required
def profile_emailverify(request):
    send_email_confirmation(request, request.user)
    return redirect('profile-settings')


@login_required
def profile_delete_view(request):
    user = request.user
    if request.method == "POST":
        logout(request)
        user.delete()
        messages.success(request, 'Account deleted, what a pity')
        return redirect('home')
    
    return render(request, 'a_users/profile_delete.html')


@login_required
def generate_bio_view(request):
    """Generate AI bio for the current user's profile"""
    if request.method == 'POST':
        profile = request.user.profile
        
        # Get data from POST request (form data sent from JavaScript)
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        profession = request.POST.get('profession', '').strip()
        location = request.POST.get('location', '').strip()
        interests = request.POST.get('interests', '').strip()
        
        # Check if user has provided any data
        has_data = any([first_name, last_name, profession, location, interests])
        
        if not has_data:
            return JsonResponse({
                'success': False,
                'message': 'Please fill in at least one field (profession, location, or interests) to generate a bio.'
            })
        
        # Temporarily update profile with new data for bio generation
        # (without saving to database yet)
        profile.first_name = first_name or profile.first_name
        profile.last_name = last_name or profile.last_name
        profile.profession = profession or profile.profession
        profile.location = location or profile.location
        profile.interests = interests or profile.interests
        
        # Generate bio
        bio = generate_user_bio(profile)
        
        if bio:
            return JsonResponse({
                'success': True,
                'bio': bio,
                'message': 'Bio generated successfully!'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to generate bio. Make sure Ollama is running.'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})
