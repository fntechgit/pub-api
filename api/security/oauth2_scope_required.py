import logging
import re
import os
import json

from django.contrib.admindocs.views import simplify_regex
from django.core.exceptions import PermissionDenied
from django.utils.functional import wraps
from django.utils.translation import ugettext_lazy as _
from api.utils import config, is_empty

_PATH_PARAMETER_COMPONENT_RE = re.compile(
    r'<(?:(?P<converter>[^>:]+):)?(?P<parameter>\w+)>'
)


def oauth2_scope_required():
    """
      Decorator to make a view only accept particular scopes:
    """
    def decorator(func):
        @wraps(func)
        def inner(view, *args, **kwargs):

            request = view.request
            token_info = request.auth

            # shortcircuit
            if os.getenv("ENV") == 'test':
                return func(view, token_info = {}, *args, **kwargs)

            path = simplify_regex(request.resolver_match.route)
            # Strip Django 2.0 convertors as they are incompatible with uritemplate format
            path = re.sub(_PATH_PARAMETER_COMPONENT_RE, r'{\g<parameter>}', path)
            path = path.replace('{pk}', '{id}')
            method = str(request.method).lower()

            logging.getLogger('oauth2').debug('endpoint {method} {path}'.format(method=method, path=path))

            endpoints = config('OAUTH2.CLIENT.ENDPOINTS')

            if token_info is None:
                logging.getLogger('oauth2').warning(
                    'oauth2_scope_required::decorator token info not present')
                raise PermissionDenied(_("token info not present."))

            logging.getLogger('oauth2').debug('oauth2_scope_required::decorator token_info {}'.format(
                json.dumps(token_info)
            ))

            endpoint = endpoints[path] if path in endpoints else None
            if not endpoint:
                logging.getLogger('oauth2').warning(
                    'oauth2_scope_required::decorator endpoint info not present')
                raise PermissionDenied(_("endpoint info not present."))

            endpoint = endpoint[method] if method in endpoint else None
            if not endpoint:
                logging.getLogger('oauth2').warning('endpoint info not present')
                raise PermissionDenied(_("endpoint info not present."))

            required_scope = endpoint['scopes'] if 'scopes' in endpoint else None

            if is_empty(required_scope):
                logging.getLogger('oauth2').warning('require scope is empty')
                raise PermissionDenied(_("required scope not present."))

            if 'scope' in token_info:
                current_scope = token_info['scope']

                logging.getLogger('oauth2').debug('current scope {current} required scope {required}'.
                                                  format(current=current_scope, required=required_scope))
                # check origins
                # check scopes

                if len(set.intersection(set(required_scope.split()), set(current_scope.split()))):
                    return func(view, token_info=token_info, *args, **kwargs)

            logging.getLogger('oauth2').warning(
                'oauth2_scope_required::decorator token scopes not present')
            raise PermissionDenied(_("token scopes not present"))
        return inner
    return decorator
