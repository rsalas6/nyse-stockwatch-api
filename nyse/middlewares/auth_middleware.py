from django.http import JsonResponse
from django.conf import settings
from django.urls import resolve

class TokenAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.api_token = settings.API_ACCESS_TOKEN

    def __call__(self, request):
        excluded_paths = ["/swagger/", "/redoc/", "/swagger.json", "/admin/"]
        current_path = resolve(request.path_info).route

        if not any(path in current_path for path in excluded_paths):
            token = request.headers.get("Authorization")
            if not token or token != f"Bearer {self.api_token}":
                return JsonResponse({"detail": "Unauthorized: Invalid token"}, status=401)

        response = self.get_response(request)
        return response
