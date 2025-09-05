# Créez un fichier middleware.py
import sys
from io import StringIO

class SuppressGLibWarnings:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Redirige les warnings GLib
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        
        response = self.get_response(request)
        
        # Restaure la sortie standard
        sys.stderr = old_stderr
        return response