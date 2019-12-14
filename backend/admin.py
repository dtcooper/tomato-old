from django.contrib import admin
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.html import format_html, mark_safe, escape


from .models import Asset, Rotator, RotatorAsset, StopSet, StopSetRotator


class ModelAdmin(admin.ModelAdmin):
    save_on_top = True

    class Media:
        js = ('admin/js/backend/rotator_color.js',)


class DisplayColorMixin:
    def display_color(self, obj):
        return format_html('<div class="color-preview" style="width: 8em; height: 3em; '
                           'border: 1px solid #333; display: inline-block;{}"></div>',
                           f'background-color: #{obj.color}' if isinstance(obj, Rotator) else '')
    display_color.short_description = 'Display Color'


class EnabledBeginEndMixin:
    def is_currently_enabled(self, obj):
        now = timezone.now()
        return (obj.enabled and (obj.begin is None or obj.begin < now)
                and (obj.end is None or obj.end > now))
    is_currently_enabled.boolean = True
    is_currently_enabled.short_description = 'Currently Enabled?'
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
            return 'Always Airs'
    enabled_dates.short_description = 'Air Dates'
    enabled_dates.admin_order_field = Coalesce('begin', 'end')


class NumAssetsMixin:
    def num_assets(self, obj):
        if isinstance(obj, StopSet):
            filter_kwargs = {'rotators__in': obj.rotators.all()}
        else:
            filter_kwargs = {'rotators': obj}

        num_enabled = Asset.objects.filter(**filter_kwargs).currently_enabled().count()
        num_disabled = Asset.objects.filter(**filter_kwargs).count() - num_enabled

        if num_enabled == num_disabled == 0:
            s = mark_safe('<em>None</em>')
        else:
            s = f'{num_enabled} Enabled'
            if num_disabled > 0:
                s += f' / {num_disabled} Disabled'
        return s
    num_assets.short_description = 'Total Audio Assets'


class RotatorInlineBase(DisplayColorMixin):
    extra = 0
    min_num = 1
    fields = ('rotator', 'display_color')
    readonly_fields = ('display_color',)

    def get_formset(self, request, obj, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        widget = formset.form.base_fields['rotator'].widget
        widget.can_add_related = False
        widget.can_change_related = False
        return formset


class StopSetRotatorInline(RotatorInlineBase, admin.TabularInline):
    model = StopSetRotator


class StopSetModelAdmin(EnabledBeginEndMixin, NumAssetsMixin, ModelAdmin):
    inlines = (StopSetRotatorInline,)
    icon_name = 'queue_music'
    readonly_fields = ('is_currently_enabled_reason',)
    list_display = ('name', 'rotator_entry_list', 'is_currently_enabled',
                    'enabled_dates', 'num_assets')

    def rotator_entry_list(self, obj):
        rotator_entries = list(StopSetRotator.objects.filter(stopset=obj).order_by(
            'id').values_list('rotator__name', 'rotator__color'))

        if rotator_entries:
            html = '<br>'.join(
                f'<span style="background-color: #{color}">{num}. {escape(name)}</span>'
                for num, (name, color) in enumerate(rotator_entries, 1))
        else:
            html = '<em>None</em>'

        return mark_safe(html)
    rotator_entry_list.short_description = 'Rotator Entries'

    def get_fieldsets(self, request, obj):
        return (
            (None, {'fields': ('name',)}),
            ('Eligibility', {
                'fields': (
                    ('is_currently_enabled_reason',) if obj else ()) + (
                        'weight', 'enabled', 'begin', 'end'),
            }),
        )


class RotatorModelAdmin(DisplayColorMixin, NumAssetsMixin, ModelAdmin):
    icon_name = 'library_music'
    readonly_fields = ('display_color',)
    list_display = ('name', 'stopset_list', 'display_color', 'num_assets')

    def stopset_list(self, obj):
        stopsets = list(obj.stopsets.distinct().order_by('name').values_list(
            'name', flat=True))
        if stopsets:
            html = '<br>'.join(
                f'&bull; {escape(name)}' for num, name in enumerate(stopsets, 1))
        else:
            html = '<em>None</em>'
        return mark_safe(html)
    stopset_list.short_description = 'Stop Sets'


class RotatorAssetInline(RotatorInlineBase, admin.StackedInline):
    model = RotatorAsset
    ordering = ('rotator__name',)


class AssetModelAdmin(EnabledBeginEndMixin, ModelAdmin):
    icon_name = 'music_note'
    inlines = (RotatorAssetInline,)
    list_display = ('view_name', 'rotator_list', 'is_currently_enabled',
                    'enabled_dates', 'list_audio_player')
    readonly_fields = ('audio_player', 'is_currently_enabled_reason', 'rotator_list')
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

    def rotator_list(self, obj):
        rotators = list(obj.rotators.order_by('name').values_list('name', 'color'))
        if rotators:
            html = '<br>'.join(
                f'&bull; <span style="background-color: #{color}">{escape(name)}</span>'
                for name, color in rotators)
        else:
            html = '<em>None</em>'
        return mark_safe(html)
    rotator_list.short_description = 'Rotators'

    def audio_player(self, obj):
        return format_html('<audio src="{}" style="width: 100%" preload="auto" controls />',
                           obj.audio.url)
    audio_player.short_description = 'Audio Player'

    def list_audio_player(self, obj):
        return format_html('<audio src="{}" style="width: 250px" preload="auto" controls />',
                           obj.audio.url)
    list_audio_player.short_description = 'Audio Player'


admin.site.register(StopSet, StopSetModelAdmin)
admin.site.register(Rotator, RotatorModelAdmin)
admin.site.register(Asset, AssetModelAdmin)
