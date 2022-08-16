from functools import wraps
import inspect
from django.apps import apps as django_apps
from injector import inject as inject_


# see https://github.com/blubber/django_injector/issues/10
def inject(func):

    signature = inspect.signature(func)
    is_method = 'self' in signature.parameters  # There must be a better way to do this

    func = inject_(func)

    @wraps(func)
    def wrapper(*args, **kwargs):
        injector = django_apps.get_app_config('django_injector').injector

        if is_method:
            self_, *args = args
        else:
            self_ = None

        return injector.call_with_injection(func, self_=self_, args=tuple(args), kwargs=kwargs)

    return wrapper
