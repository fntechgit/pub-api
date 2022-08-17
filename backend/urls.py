from django.conf import settings
from django.conf.urls.static import static
from api.urls import private_urlpatterns as private_api_v1
from django.urls import path, include
from rest_framework.schemas import get_schema_view
from api.views.openapi_schema import PubApiSchemaGenerator

api_urlpatterns = [
    path('v1/',  include(private_api_v1)),
]

urlpatterns = [
    path('api/', include(api_urlpatterns)),
    path('openapi', get_schema_view(
        generator_class=PubApiSchemaGenerator,
        title="Pub API",
        description="Supabase Publisher API",
        version="1.0.0",
        patterns=api_urlpatterns,
    ), name='openapi-schema'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)