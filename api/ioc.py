from injector import Module, singleton

from api.security.abstract_access_token_service import AbstractAccessTokenService
from api.security.access_token_service import AccessTokenService
from api.models.supabase_pub_service import SupaBasePubService
from api.models.abstract_pub_service import AbstractPubService


# define here all root ioc bindings
class ApiAppModule(Module):
    def configure(self, binder):
        # services
        access_token_service = AccessTokenService()
        binder.bind(AbstractAccessTokenService, to=access_token_service, scope=singleton)

        supabase_pub_service = SupaBasePubService()
        binder.bind(AbstractPubService, to=supabase_pub_service, scope=singleton )
