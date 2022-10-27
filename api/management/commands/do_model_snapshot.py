from django.core.management.base import BaseCommand, CommandError
from django_injector import inject

from api.models.feeds_download_service import FeedsDownloadService
from api.models.feeds_upload_service import FeedsUploadService

DOWNLOAD = 'download'
UPLOAD = 'upload'
FULL = 'full'


class Command(BaseCommand):
    help = 'Upload summit models json to S3'

    @inject
    def __init__(self, feeds_download_service: FeedsDownloadService, feeds_upload_service: FeedsUploadService):
        super().__init__()
        self.feeds_download_service = feeds_download_service
        self.feeds_upload_service = feeds_upload_service

    def add_arguments(self, parser):
        parser.add_argument('summit_id', type=int)
        parser.add_argument(
            '-o', '--operation',
            default=FULL,
            choices=(
                DOWNLOAD,
                UPLOAD,
                FULL
            )
        )

    def handle(self, *args, **options):
        op: str = options.get('operation')
        summit_id: int = options.get('summit_id')

        if op in [DOWNLOAD, FULL]:
            self.feeds_download_service.download(summit_id)

        if op in [UPLOAD, FULL]:
            self.feeds_upload_service.upload(summit_id)
