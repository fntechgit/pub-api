from django.urls import path, include
from .views import EntityUpdatesCreateAPIView

entity_updates_patterns = ([
                               path('entity-updates', EntityUpdatesCreateAPIView.as_view(
                                   {
                                       'post': 'create',
                                   }
                               ),
                                    name='create'),
                           ], 'entity_updates')

private_urlpatterns = [
    path('summits/<int:summit_id>/', include(entity_updates_patterns)),
]
