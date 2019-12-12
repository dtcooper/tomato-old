from django.contrib import admin
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.html import format_html, mark_safe


from .models import Asset, Rotation, RotationAsset, StopSet, StopSetRotation


class ModelAdmin(admin.ModelAdmin):
    save_on_top = True


class DisplayColorMixin:
    def display_color(self, obj):
        return mark_safe('<div class="color-preview" style="width: 8em; height: 3em; '
                         'border: 1px solid #333; display: inline-block;"></div>')
    display_color.short_description = 'Display Color'


class EnabledBeginEndMixin:
    def is_currently_enabled(self, obj):
        now = timezone.now()
        return (obj.enabled and (obj.begin is None or obj.begin < now)
                and (obj.end is None or obj.end > now))
    is_currently_enabled.boolean = True
    is_currently_enabled.short_description = 'Enabled?'
    # TODO: figure out a way to express this in SQL and then sort by it

    def is_currently_enabled_reason(self, obj):
        reasons = []
        if not obj.enabled:
            reasons.append('via checkbox')

        now = timezone.now()
        if obj.begin is not None and now < obj.begin:
            reasons.append('Begin Date in the future')
        if obj.end is not None and now > obj.end:
            reasons.append('End Date in the past')

        return f'Disabled: {", ".join(reasons)}' if reasons else 'Enabled'
    is_currently_enabled_reason.short_description = 'Currently Enabled?'

    def rotation_list(self, obj):
        return ', '.join(obj.rotations.values_list('name', flat=True))
    rotation_list.short_description = 'Rotations'

    def enabled_dates(self, obj):
        tz = timezone.get_default_timezone()
        fmt = '%a %b %-d %Y %-I:%M %p'

        if obj.begin and obj.end:
            return format_html(
                '<b>Begins:</b> {}<br><b>Ends:</b> {}',
                tz.normalize(obj.begin).strftime(fmt),
                tz.normalize(obj.end).strftime(fmt))
        elif obj.begin:
            return format_html(
                '<b>Begins:</b> {}', tz.normalize(obj.begin).strftime(fmt))
        elif obj.end:
            return format_html(
                '<b>Ends:</b> {}', tz.normalize(obj.end).strftime(fmt))
        else:
            return 'Always'
    enabled_dates.short_description = 'Air Dates'
    enabled_dates.admin_order_field = Coalesce('begin', 'end')


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


class StopSetModelAdmin(EnabledBeginEndMixin, ModelAdmin):
    inlines = (StopSetRotationInline,)
    icon_name = 'queue_music'
    readonly_fields = ('is_currently_enabled_reason',)
    list_display = ('__str__', 'is_currently_enabled', 'rotation_list', 'assets')

    def assets(self, obj):
        num_enabled = Asset.objects.filter(rotations__in=obj.rotations.all()).currently_enabled().count()
        num_disabled = Asset.objects.filter(rotations__in=obj.rotations.all()).count() - num_enabled
        s = f'{num_enabled} Enabled'
        if num_disabled > 0:
            s += f' / {num_disabled} Disabled'
        return s
    assets.short_description = 'Total Assets'

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


class AssetModelAdmin(EnabledBeginEndMixin, ModelAdmin):
    icon_name = 'music_note'
    inlines = (RotationAssetInline,)
    list_display = ('view_name', 'rotation_list', 'is_currently_enabled',
                    'enabled_dates', 'list_audio_player')
    readonly_fields = ('audio_player', 'is_currently_enabled_reason', 'rotation_list')
    ordering = ('name',)

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

    def view_name(self, obj):  # Get rid of "Optional Name"
        return obj.name
    view_name.short_description = 'Name'
    view_name.admin_order_field = 'name'

    def audio_player(self, obj):
        return format_html('<audio src="{}" style="width: 100%" preload="auto" controls></audio>',
                           obj.audio.url)
    audio_player.short_description = 'Audio Player'

    def list_audio_player(self, obj):
        return format_html('<audio src="{}" style="width: 250px" preload="auto" controls></audio>',
                           obj.audio.url)
    list_audio_player.short_description = 'Audio Player'


admin.site.register(StopSet, StopSetModelAdmin)
admin.site.register(Rotation, RotationModelAdmin)
admin.site.register(Asset, AssetModelAdmin)
