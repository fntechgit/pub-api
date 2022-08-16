import logging
import traceback
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from ..security import OAuth2Authentication, oauth2_scope_required
from ..serializers import EntityUpdateWriteSerializer
from rest_framework.settings import api_settings
import os


class EntityUpdatesCreateAPIView(ViewSet):
    authentication_classes = [] if os.getenv("ENV") == 'test' else [OAuth2Authentication]

    serializer_class = EntityUpdateWriteSerializer

    @staticmethod
    def perform_create(serializer):
        serializer.save()

    @staticmethod
    def get_success_headers(data):
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}

    @oauth2_scope_required()
    def create(self, request, summit_id, *args, **kwargs):
        try:
            logging.getLogger('api').debug('calling EntityUpdatesCreateAPIView::create')
            serializer = EntityUpdateWriteSerializer(data=request.data, context={
                "summit_id": summit_id})
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        except ValidationError as e:
            logging.getLogger('api').warning(e)
            return Response(e.detail, status=status.HTTP_412_PRECONDITION_FAILED)
        except:
            logging.getLogger('api').error(traceback.format_exc())
            return Response('server error', status=status.HTTP_500_INTERNAL_SERVER_ERROR)
