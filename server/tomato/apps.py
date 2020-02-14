from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured

try:
    import sox  # noqa
except ImportError:
    raise ImproperlyConfigured('sox package must be installed')


class TomatoConfig(AppConfig):
    name = 'tomato'
    verbose_name = 'Radio Automation'

    def ready(self):
        from constance.apps import ConstanceConfig

        ConstanceConfig.verbose_name = 'Tomato Configuration'

        # Create permission here, re:
        # - https://github.com/jazzband/django-constance/blob/master/constance/apps.py
