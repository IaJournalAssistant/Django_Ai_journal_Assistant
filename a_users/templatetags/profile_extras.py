"""
Custom template tags and filters for user profiles
"""
from django import template

register = template.Library()


@register.filter
def split_interests(value):
    """
    Split comma-separated interests into a list
    
    Usage: {{ profile.interests|split_interests }}
    """
    if not value:
        return []
    return [interest.strip() for interest in value.split(',') if interest.strip()]

