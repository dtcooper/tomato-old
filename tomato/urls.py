from django.contrib import admin
from django.urls import path


admin.site.site_url = None
admin.site.site_title = admin.site.site_header = 'Tomato Radio Automation Administration'
admin.site.show_themes = True

urlpatterns = [
    path('', admin.site.urls),
]
