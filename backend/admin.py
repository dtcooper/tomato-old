from django.contrib import admin
from django.utils.html import mark_safe


from .models import AssetRotation, StopSet, StopSetEntry


class DisplayColorMixin:
    def display_color(self, obj):
        return mark_safe('<div class="color-preview" style="width: 8em; height: 3em; '
                         'border: 1px solid #333; display: inline-block;"></div>')
    display_color.short_description = 'Display Color'


class StopSetEntryInline(DisplayColorMixin, admin.TabularInline):
    model = StopSetEntry
    extra = 0
    fields = ('asset_rotation', 'display_color')
    readonly_fields = ('display_color',)

    def get_formset(self, request, obj, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        widget = formset.form.base_fields['asset_rotation'].widget
        widget.can_add_related = False
        widget.can_change_related = False
        return formset


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


class AssetRotationModelForm(DisplayColorMixin, admin.ModelAdmin):
    icon_name = 'radio'
    readonly_fields = ('display_color',)


admin.site.register(StopSet, StopSetEntryModelAdmin)
admin.site.register(AssetRotation, AssetRotationModelForm)
