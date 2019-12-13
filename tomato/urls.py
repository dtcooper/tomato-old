from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.utils.html import mark_safe, escape
from django.templatetags.static import static as static_url


logo_img = (f'<img src="{escape(static_url("admin/images/backend/tomato.png"))}" '
            'style="height: 32px; width: 32px">')

admin.site.site_url = None
admin.site.site_title = admin.site.site_header = mark_safe(
    f'{logo_img} Tomato Radio Automation {logo_img}')
admin.site.show_themes = True

urlpatterns = [
    path('', admin.site.urls),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
