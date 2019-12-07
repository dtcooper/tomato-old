from django.contrib import admin
from django.utils.html import format_html, mark_safe


from .models import Asset, Rotation, RotationAsset, StopSet, StopSetRotation


class ModelAdmin(admin.ModelAdmin):
    save_on_top = True


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


class StopSetRotationEntryModelAdmin(ModelAdmin):
    inlines = (StopSetRotationInline,)
    icon_name = 'queue_music'
    readonly_fields = ('is_currently_enabled_reason',)
    list_display = ('__str__', 'is_currently_enabled')

    def get_fieldsets(self, request, obj):
        return (
            (None, {'fields': ('name',)}),
            ('Eligibility', {
                'fields': (
                    ('is_currently_enabled_reason',) if obj else ()) + (
                        'weight', 'enabled', 'begin', 'end'),
            }),
        )


class RotationModelAdmin(DisplayColorMixin, ModelAdmin):
    icon_name = 'library_music'
    readonly_fields = ('display_color',)


class RotationAssetInline(RotationInlineBase, admin.StackedInline):
    model = RotationAsset
    min_num = 1
    ordering = ('rotation__name',)


class AssetModelAdmin(ModelAdmin):
    icon_name = 'music_note'
    inlines = (RotationAssetInline,)
    list_display = ('__str__', 'is_currently_enabled', 'rotation_list')
    readonly_fields = ('audio_player', 'is_currently_enabled_reason', 'rotation_list')

    def get_fieldsets(self, request, obj):
        return (
            (None, {
                'fields': ('name', 'audio') + (('audio_player',) if obj else ()),
            }),
            ('Eligibility', {
                'fields': (
                    ('is_currently_enabled_reason',) if obj else ()) + (
                        'weight', 'enabled', 'begin', 'end'),
            }),
        )

    def rotation_list(self, obj):
        return ', '.join(obj.rotations.values_list('name', flat=True))
    rotation_list.short_description = 'Rotations'

    def audio_player(self, obj):
        return format_html('<audio src="{}" style="width: 100%" preload="auto" controls></audio>',
                           obj.audio.url)


admin.site.register(StopSet, StopSetRotationEntryModelAdmin)
admin.site.register(Rotation, RotationModelAdmin)
admin.site.register(Asset, AssetModelAdmin)
