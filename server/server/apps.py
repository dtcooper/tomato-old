from django.apps import AppConfig


class ServerConfig(AppConfig):
    name = 'server'

    def ready(self):
        from constance.apps import ConstanceConfig

        ConstanceConfig.verbose_name = 'Tomato Configuration'
