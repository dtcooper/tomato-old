from django.contrib import admin
from django.utils.html import format_html, mark_safe


from .models import AssetRotation, StopSet, StopSetEntry


# class BimmerAdminSite(admin.AdminSite):
#     site_header = 'Monty Python administration'
# TODO: just use site admin, unregister user/group models

# https://stackoverflow.com/questions/398163/ordering-admin-modeladmin-objects
# Can be done in middleware, process_template by reordering context variable


class StopSetEntryInline(admin.StackedInline):
    model = StopSetEntry
    extra = 0
    fields = ('asset_rotation', 'ordering', 'color')
    readonly_fields = ('color',)

    def get_formset(self, request, obj, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        widget = formset.form.base_fields['asset_rotation'].widget
        widget.can_add_related = False
        widget.can_change_related = False
        return formset

    def color(self, instance):
        return format_html(
            '<p style="background-color: #{}; padding: 4px 10px">{}</p>',
            instance.asset_rotation.color, instance.asset_rotation.get_color_display())
    color.short_description = 'Color'

    def get_queryset(self, request):
        return super().get_queryset(request).ordered()


class StopSetEntryModelAdmin(admin.ModelAdmin):
    inlines = (StopSetEntryInline,)
    icon_name = 'radio'
    fieldsets = (
        (None, {
            'fields': ('name',),
        }),
        ('Eligibility', {
            'fields': ('weight', 'enabled', 'begin', 'end'),
        }),
    )
    list_display = ('__str__',)

    class Media:
        js = ('admin/js/stop_set.js',)


class AssetRotationModelForm(admin.ModelAdmin):
    icon_name = 'radio'
    readonly_fields = ('color_preview',)

    def color_preview(self, obj):
        return mark_safe('<div id="id_color_preview" style="width: 7em; '
                         'height: 3em; border: 1px solid #333"></div>')
    color_preview.short_description = 'Color Preview'

    class Media:
        js = ('admin/js/asset_rotation.js',)


admin.site.register(StopSet, StopSetEntryModelAdmin)
admin.site.register(AssetRotation, AssetRotationModelForm)
