from django import template
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def add_days(date, days):
    """Add days to a date"""
    if isinstance(date, datetime):
        return date + timedelta(days=int(days))
    return date

@register.filter
def get_item_by_date(logs, target_date):
    """Get log item by date from a list of logs"""
    if not logs:
        return None
    
    for log in logs:
        if hasattr(log, 'date') and log.date == target_date:
            return log
    return None