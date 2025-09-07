from django import template

register = template.Library()

@register.filter
def div(value, arg):
    """Division filter"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiplication filter"""
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0

@register.filter
def abs(value):
    """Absolute value filter"""
    try:
        return abs(float(value))
    except ValueError:
        return 0
    
    
    
    
    
    
    
    
    