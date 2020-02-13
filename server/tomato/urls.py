from django.urls import path

from .views import auth, export, ping


urlpatterns = [
    path('ping', ping, name='ping'),
    path('auth', auth, name='auth'),
    path('export', export, name='export'),
]
