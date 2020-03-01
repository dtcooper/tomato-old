from django.urls import path

from .views import auth, export, ping, token_login


urlpatterns = [
    path('auth', auth, name='auth'),
    path('export', export, name='export'),
    path('ping', ping, name='ping'),
    path('token-login', token_login, name='token-login'),
]
