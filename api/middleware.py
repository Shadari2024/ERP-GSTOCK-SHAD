class NoHTMLRedirectMiddleware:
    """
    Middleware pour empêcher les redirections HTML pour les requêtes API
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Vérifier si c'est une requête API et une redirection
        if (request.path.startswith('/api/') and 
            response.status_code in [302, 301] and 
            'text/html' in response.get('Content-Type', '')):
            
            # Retourner une erreur JSON au lieu de rediriger
            from django.http import JsonResponse
            return JsonResponse(
                {'error': 'Authentication required', 'login_url': response.url},
                status=401
            )
        
        return response