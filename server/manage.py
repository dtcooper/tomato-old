#!/usr/bin/env python
import os
import sys


def show_toolbar(request):
    if request.is_ajax():
        return False
    return True


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

    try:
        from django.conf import settings
        from django.core.management import execute_from_command_line
        from django.core.management.commands.runserver import Command as runserver
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    if settings.DEBUG and len(sys.argv) >= 2 and sys.argv[1] == 'runserver':
        settings.INSTALLED_APPS.append('debug_toolbar')
        settings.MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
        settings.DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': 'manage.show_toolbar'}

    runserver.default_addr = '0.0.0.0'

    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
