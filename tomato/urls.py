from django.conf import settings
from django.contrib import admin
from django.urls import include, path


admin.site.site_url = None
admin.site.site_title = admin.site.site_header = 'Tomato Radio Automation Administration'
admin.site.show_themes = True

urlpatterns = [
    path('', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
