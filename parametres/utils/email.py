# utils/email.py
from django.core.mail import EmailMessage, get_connection
from django.conf import settings

def send_email_with_company_config(entreprise, subject, message, recipient_list, attachments=None):
    """
    Envoie un email en utilisant la configuration SMTP de l'entreprise
    """
    config = getattr(entreprise, "config_saas", None)
    if not config:
        raise Exception("Configuration SAAS non trouvée pour cette entreprise")

    connection = get_connection(
        backend=settings.EMAIL_BACKEND,
        host=config.email_host,
        port=config.email_port,
        username=config.email_host_user,
        password=config.email_host_password,
        use_tls=config.email_use_tls,
    )

    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=config.get_from_email(),
        to=recipient_list,
        connection=connection
    )

    if attachments:
        for filename, content, mimetype in attachments:
            email.attach(filename, content, mimetype)

    email.send(fail_silently=False)
    return True
