from .models import JournalActivite

def get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def enregistrer_activite(user, action, details, ip_address):
    JournalActivite.objects.create(
        utilisateur=user,
        action=action,
        details=details,
        ip_address=ip_address
    )

def has_permission(user, permission_codename):
    """Vérifie si l'utilisateur a une permission spécifique"""
    return user.user_permissions.filter(codename=permission_codename).exists() or \
           user.groups.filter(permissions__codename=permission_codename).exists()
           
           
           
           # security/utils.py
