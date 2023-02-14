from injector import Module, singleton

from api.models import AbstractPubService
from api.models.abstract_feeds_upload_service import AbstractFeedsUploadService
from api.models.abstract_feeds_download_service import AbstractFeedsDownloadService
from api.models.feeds_download_service import FeedsDownloadService
from api.security.abstract_access_token_service import AbstractAccessTokenService
from api.security.access_token_service import AccessTokenService
from api.models.feeds_upload_service import FeedsUploadService
from api.models.supabase_pub_service import SupaBasePubService
from api.models.redis_ws_pub_service import RedisWSPubService
from api.models.ably_pub_service import AblyPubService
from api.models.pub_manager import PubManager
from api.models.abstract_pub_manager import AbstractPubManager


# define here all root ioc bindings
class ApiAppModule(Module):
    def configure(self, binder):
        # services
        access_token_service = AccessTokenService()
        binder.bind(AbstractAccessTokenService, to=access_token_service, scope=singleton)

        supabase_pub_service = SupaBasePubService()
        binder.bind(AbstractPubService, to=supabase_pub_service, scope=singleton)

        pub_manager = PubManager()
        pub_manager.add_service(supabase_pub_service)
        pub_manager.add_service(RedisWSPubService())
        pub_manager.add_service(AblyPubService())

        binder.bind(AbstractPubManager, to=pub_manager, scope=singleton)

        feeds_download_service = FeedsDownloadService(access_token_service)
        binder.bind(AbstractFeedsDownloadService, to=feeds_download_service, scope=singleton)

        feeds_upload_service = FeedsUploadService(pub_manager)
        binder.bind(AbstractFeedsUploadService, to=feeds_upload_service, scope=singleton)