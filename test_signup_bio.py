"""
Test script to verify signup and bio generation
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'a_core.settings')
django.setup()

from django.contrib.auth.models import User
from a_users.models import Profile
from a_users.ai_service import generate_user_bio

# Check existing users
print("=" * 60)
print("Checking existing users and their profiles:")
print("=" * 60)

users = User.objects.all()
for user in users:
    try:
        profile = user.profile
        print(f"\nUser: {user.username}")
        print(f"  First Name: {profile.first_name or '(empty)'}")
        print(f"  Last Name: {profile.last_name or '(empty)'}")
        print(f"  Profession: {profile.profession or '(empty)'}")
        print(f"  Location: {profile.location or '(empty)'}")
        print(f"  Interests: {profile.interests or '(empty)'}")
        print(f"  Bio: {profile.info[:80] + '...' if profile.info and len(profile.info) > 80 else profile.info or '(empty)'}")
        
        # Offer to generate bio if missing
        if not profile.info:
            has_data = any([
                profile.first_name,
                profile.last_name,
                profile.profession,
                profile.interests,
                profile.location
            ])
            if has_data:
                print(f"\n  → User has data but no bio. Generating...")
                bio = generate_user_bio(profile)
                if bio:
                    profile.info = bio
                    profile.save()
                    print(f"  ✓ Bio generated: {bio[:80]}...")
                else:
                    print(f"  ✗ Bio generation failed (is Ollama running?)")
    except Profile.DoesNotExist:
        print(f"\nUser: {user.username} - No profile!")

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)

