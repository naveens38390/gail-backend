# project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def api_root(request):
    """Simple root endpoint to prevent 404"""
    return JsonResponse({
        "message": "GAIL Backend API",
        "status": "running",
        "endpoints": {
            "admin": "/admin/",
            "api": "/api/",
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin panel
    path('api/', include('gail_app.urls')),  # API routes
    path('', api_root, name='api_root'),  # ADD THIS LINE - fixes root URL 404
]

# Add media files serving for development (ADD THIS BLOCK)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)