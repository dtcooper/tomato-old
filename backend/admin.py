from django.contrib import admin
from django.utils.html import format_html, mark_safe


from .models import Asset, Rotation, StopSet, StopSetRotation


class DisplayColorMixin:
    def display_color(self, obj):
        return mark_safe('<div class="color-preview" style="width: 8em; height: 3em; '
                         'border: 1px solid #333; display: inline-block;"></div>')
    display_color.short_description = 'Display Color'


class RotationInlineBase(DisplayColorMixin):
    extra = 0
    min_num = 1
    fields = ('rotation', 'display_color')
    readonly_fields = ('display_color',)

    def get_formset(self, request, obj, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        widget = formset.form.base_fields['rotation'].widget
        widget.can_add_related = False
        widget.can_change_related = False
        return formset


class StopSetRotationInline(RotationInlineBase, admin.TabularInline):
    model = StopSetRotation


class StopSetRotationModelAdmin(admin.ModelAdmin):
    inlines = (StopSetRotationInline,)
    icon_name = 'queue_music'
    fieldsets = (
        (None, {
            'fields': ('name',),
        }),
        ('Eligibility', {
            'fields': ('is_currently_enabled', 'weight', 'enabled', 'begin', 'end'),
        }),
    )
    list_display = ('__str__',)


class RotationModelAdmin(DisplayColorMixin, admin.ModelAdmin):
    icon_name = 'library_music'
    readonly_fields = ('display_color',)


class AssetRotationsInline(RotationInlineBase, admin.StackedInline):
    model = Asset.rotations.through


class AssetModelAdmin(admin.ModelAdmin):
    icon_name = 'music_note'
    inlines = (AssetRotationsInline,)
    list_display = ('__str__', 'is_currently_enabled')
    fieldsets = (
        (None, {
            'fields': ('name', 'audio', 'audio_player'),
        }),
        ('Eligibility', {
            'fields': ('is_currently_enabled_reason', 'weight', 'enabled', 'begin', 'end'),
        }),
    )
    readonly_fields = ('audio_player', 'is_currently_enabled_reason')

    def get_fieldsets(self, request, obj):
        # TODO: Remove currently enabled and audio player for assets that don't exis
        return super().get_fieldsets(request, obj)

    def audio_player(self, obj):
        return format_html('<audio src="{}" style="width: 100%" preload="auto" controls></audio>', obj.audio.url)


admin.site.register(StopSet, StopSetRotationModelAdmin)
admin.site.register(Rotation, RotationModelAdmin)
admin.site.register(Asset, AssetModelAdmin)
