from django.urls import path

from .views import export


urlpatterns = [
    path('export', export, name='export'),
]
