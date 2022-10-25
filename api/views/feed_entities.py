import logging
import traceback
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from ..security import OAuth2Authentication, oauth2_scope_required
from api.tasks import create_model_snapshot
import os


class EntityFeedAPIView(ViewSet):
    authentication_classes = [] if os.getenv("ENV") == 'test' else [OAuth2Authentication]

    #@oauth2_scope_required()
    def feed(self, request, summit_id, *args, **kwargs):
        try:
            logging.getLogger('api').debug(f'calling EntityFeedAPIView::feed for summit_id {summit_id}')
            create_model_snapshot.delay(summit_id)
            return Response(status=status.HTTP_201_CREATED)
        except:
            logging.getLogger('api').error(traceback.format_exc())
            return Response('server error', status=status.HTTP_500_INTERNAL_SERVER_ERROR)
