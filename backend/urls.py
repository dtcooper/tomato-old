from django.urls import path

from .views import authenticate, export


urlpatterns = [
    path('auth', authenticate, name='auth'),
    path('export', export, name='export')
]
