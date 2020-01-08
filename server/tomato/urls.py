from django.urls import path

from .views import authenticate, export, ping


urlpatterns = [
    path('ping', ping, name='ping'),
    path('auth', authenticate, name='auth'),
    path('export', export, name='export'),
]
