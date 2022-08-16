from django.conf import settings
from django.conf.urls.static import static
from api.urls import private_urlpatterns as private_api_v1
from django.urls import path, include

api_urlpatterns = [
    path('v1/',  include(private_api_v1)),
]

urlpatterns = [
    path('api/', include(api_urlpatterns)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)