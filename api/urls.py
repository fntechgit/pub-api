from django.urls import path, include

from .views import EntityUpdatesCreateAPIView
from .views.feed_entities import EntityFeedAPIView

entity_updates_patterns = (
    [
        path('entity-updates', EntityUpdatesCreateAPIView.as_view({'post': 'create'}), name='create'),
    ],
    'entity_updates'
)

show_models_feed_patterns = (
    [
        path('show_models_feed', EntityFeedAPIView.as_view({'post': 'feed'}), name='feed'),
    ],
    'show_models_feed'
)

private_urlpatterns = [
    path('summits/<int:summit_id>/feeds/', include(show_models_feed_patterns)),
    path('summits/<int:summit_id>/', include(entity_updates_patterns)),
]
