import logging
import traceback

from django_injector import inject
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from ..models.abstract_feeds_download_service import AbstractFeedsDownloadService
from ..models.abstract_feeds_upload_service import AbstractFeedsUploadService
from ..security import OAuth2Authentication, oauth2_scope_required
from api.tasks import create_model_snapshot
import os


class EntityFeedAPIView(ViewSet):
    authentication_classes = [] if os.getenv("ENV") == 'test' else [OAuth2Authentication]

    @inject
    def __init__(self,
                 feeds_download_service: AbstractFeedsDownloadService,
                 feeds_upload_service: AbstractFeedsUploadService):
        super().__init__()
        self.feeds_download_service = feeds_download_service
        self.feeds_upload_service = feeds_upload_service

    @oauth2_scope_required()
    def feed(self, request, summit_id, *args, **kwargs):
        try:
            logging.getLogger('api').debug(f'calling EntityFeedAPIView::feed for summit_id {summit_id}')
            create_model_snapshot.delay(summit_id, self.feeds_download_service, self.feeds_upload_service)
            return Response(status=status.HTTP_201_CREATED)
        except:
            logging.getLogger('api').error(traceback.format_exc())
            return Response('server error', status=status.HTTP_500_INTERNAL_SERVER_ERROR)
