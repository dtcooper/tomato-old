from django.urls import path

from .views import authenticate


urlpatterns = [
    path('auth', authenticate, name='auth'),
]
