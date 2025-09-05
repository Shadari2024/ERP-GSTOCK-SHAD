# ventes/templatetags/math_filters.py
from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def div(value, arg):
    """Division de value par arg"""
    try:
        if value and arg:
            result = Decimal(str(value)) / Decimal(str(arg))
            return result.quantize(Decimal('0.01'))
        return Decimal('0.00')
    except (ValueError, ZeroDivisionError, InvalidOperation):
        return Decimal('0.00')