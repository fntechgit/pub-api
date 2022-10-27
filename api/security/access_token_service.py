import logging
import sys

import requests
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache

from .abstract_access_token_service import AbstractAccessTokenService
from ..utils import config


class AccessTokenService(AbstractAccessTokenService):

    def validate(self, access_token:str):
        """
              Authenticate the request, given the access token.
              """
        cached_token_info = None
        logging.getLogger('oauth2').debug('AccessTokenService::validate {access_token}'.format(access_token=access_token))
        # try get access_token from DB and check if not expired
        cached_token_info = cache.get(access_token)

        if cached_token_info is None:
            try:
                response = requests.post(
                    '{base_url}/{endpoint}'.format
                        (
                        base_url=config('OAUTH2.IDP.BASE_URL', None),
                        endpoint=config('OAUTH2.IDP.INTROSPECTION_ENDPOINT', None)
                    ),
                    auth=(config('OAUTH2.CLIENT.ID', None), config('OAUTH2.CLIENT.SECRET', None),),
                    params={'token': access_token},
                    verify=False if config('DEBUG', False) else True,
                    allow_redirects=False
                )

                if response.status_code == requests.codes.ok:
                    cached_token_info = response.json()
                    cache.set(access_token, cached_token_info, timeout=cached_token_info['expires_in'])
                else:
                    logging.getLogger('oauth2').warning(
                        'http code {code} http content {content}'.format(code=response.status_code,
                                                                         content=response.content))
                    return None
            except requests.exceptions.RequestException as e:
                logging.getLogger('oauth2').error(e)
                return None
            except:
                logging.getLogger('oauth2').error(sys.exc_info())
                return None

        return AnonymousUser, cached_token_info

    def get_access_token(self) -> str:
        response = requests.post(
            f"{config('OAUTH2.IDP.BASE_URL', None)}/{config('OAUTH2.IDP.TOKEN_ENDPOINT', None)}",
            auth=(config('OAUTH2.CONTENT_SNAPSHOT_CLIENT.ID', None), config('OAUTH2.CONTENT_SNAPSHOT_CLIENT.SECRET', None),),
            verify=False if config('DEBUG', False) else True,
            allow_redirects=False,
            data={
                "grant_type": "client_credentials",
                "scope": config('OAUTH2.CONTENT_SNAPSHOT_CLIENT.SCOPES', None)
            }
        )

        return response.json()['access_token']

