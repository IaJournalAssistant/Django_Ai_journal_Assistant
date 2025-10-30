from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from .models import Profile
from .ai_service import generate_user_bio
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)       
def user_postsave(sender, instance, created, **kwargs):
    user = instance
    
    # add profile if user is created
    if created:
        Profile.objects.create(
            user = user,
        )
    else:
        # update allauth emailaddress if exists 
        try:
            email_address = EmailAddress.objects.get_primary(user)
            if email_address.email != user.email:
                email_address.email = user.email
                email_address.verified = False
                email_address.save()
        except:
            # if allauth emailaddress doesn't exist create one
            EmailAddress.objects.create(
                user = user,
                email = user.email, 
                primary = True,
                verified = False
            )
        
        
@receiver(pre_save, sender=User)
def user_presave(sender, instance, **kwargs):
    if instance.username:
        instance.username = instance.username.lower()


@receiver(post_save, sender=Profile)
def generate_bio_on_profile_update(sender, instance, created, **kwargs):
    """
    Auto-generate bio when profile is created or updated with extended fields
    """
    # Check if profile has extended fields filled and no bio yet
    has_extended_data = any([
        instance.first_name,
        instance.last_name,
        instance.profession,
        instance.interests,
        instance.location
    ])
    
    # Generate bio if we have data and either:
    # - Profile was just created with data, OR
    # - Profile has no bio yet
    if has_extended_data and not instance.info:
        try:
            logger.info(f"Generating AI bio for user: {instance.user.username}")
            bio = generate_user_bio(instance)
            if bio:
                # Update without triggering signal again
                Profile.objects.filter(pk=instance.pk).update(info=bio)
                logger.info(f"Bio generated successfully for: {instance.user.username}")
        except Exception as e:
            logger.error(f"Error generating bio for {instance.user.username}: {str(e)}")