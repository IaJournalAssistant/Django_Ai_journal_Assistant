"""
Management command to generate bio for existing users
Run this to generate bios for users who already exist
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'a_core.settings')
django.setup()

from django.contrib.auth.models import User
from a_users.models import Profile
from a_users.ai_service import generate_user_bio

def generate_bios_for_all_users():
    """Generate bios for all users who don't have one"""
    profiles = Profile.objects.filter(info__isnull=True) | Profile.objects.filter(info='')
    
    print(f"Found {profiles.count()} profiles without bios")
    
    for profile in profiles:
        print(f"\nProcessing user: {profile.user.username}")
        
        # Check if user has any extended data
        has_data = any([
            profile.first_name,
            profile.last_name,
            profile.profession,
            profile.interests,
            profile.location
        ])
        
        if has_data:
            print(f"  - Has extended data, generating bio...")
            bio = generate_user_bio(profile)
            if bio:
                profile.info = bio
                profile.save()
                print(f"  ✓ Bio generated: {bio[:80]}...")
            else:
                print(f"  ✗ Bio generation failed")
        else:
            print(f"  - No extended data available, skipping")

if __name__ == '__main__':
    print("=" * 60)
    print("Bio Generation Script")
    print("=" * 60)
    generate_bios_for_all_users()
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

