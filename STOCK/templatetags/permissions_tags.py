from django import template

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


from django import template
from django.conf import settings



@register.simple_tag(takes_context=True)
def has_permission(context, user, permission):
    if not user.is_authenticated:
        return False
    return user.has_perm(permission) or user.is_superuser