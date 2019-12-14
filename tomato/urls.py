from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.utils.html import format_html
from django.templatetags.static import static as static_url


admin.site.site_url = None
admin.site.site_title = admin.site.site_header = format_html(
    ('<img src="{logo_url}" style="height: 32px; width: 32px">'
     ' Tomato Radio Automation '
     '<img src="{logo_url}" style="height: 32px; width: 32px">'),
    logo_url=static_url("admin/images/backend/tomato.png"))
admin.site.show_themes = False

urlpatterns = [
    path('', include('backend.urls')),
    path('', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
