from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.utils.html import format_html
from django.templatetags.static import static as static_url


icon_url = static_url("admin/images/tomato.png")
logo_img = '<img src="{url}" style="height: 40px; width: 40px; image-rendering: pixelated;">'

admin.site.site_url = None
admin.site.site_title = admin.site.site_header = format_html(
    logo_img + ' Tomato Radio Automation ' + logo_img, url=icon_url)
admin.site.show_themes = True
admin.site.favicon = icon_url

urlpatterns = [
    path('', include('server.urls')),
    path('', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
