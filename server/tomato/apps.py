from django.apps import AppConfig


class TomatoConfig(AppConfig):
    name = 'tomato'
    verbose_name = 'Radio Automation'

    def ready(self):
        from constance.apps import ConstanceConfig

        ConstanceConfig.verbose_name = 'Tomato Configuration'
