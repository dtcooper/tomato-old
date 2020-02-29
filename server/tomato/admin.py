import datetime

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm, AdminForm
from django.contrib.admin.widgets import AdminSplitDateTime
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.db.models.functions import Coalesce
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import escape, format_html, mark_safe

from .client_server_constants import COLORS
from .models import Asset, Rotator, StopSet, StopSetRotator


STRFTIME_FMT = '%a %b %-d %Y %-I:%M %p'


class TomatoUserAdmin(UserAdmin):
    empty_value_display = 'None'
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_superuser', 'groups',)}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_superuser')
    list_filter = ('is_superuser', 'is_active', 'groups')
    save_on_top = True

    def save_model(self, request, obj, form, change):
        obj.is_staff = True
        return super().save_model(request, obj, form, change)


class TomatoModelAdmin(admin.ModelAdmin):
    empty_value_display = 'None'
    list_max_show_all = 2500
    list_per_page = 100
    list_prefetch_related = None
    save_on_top = True
    search_fields = ('name',)

    def get_queryset(self, request):
        # For performance https://code.djangoproject.com/ticket/29985#comment:3
        queryset = super().get_queryset(request)
        if self.list_prefetch_related and request.resolver_match.view_name.endswith('changelist'):
            queryset = queryset.prefetch_related(self.list_prefetch_related)
        return queryset


class CurrentlyAiringListFilter(admin.SimpleListFilter):
    parameter_name = 'airing'
    title = 'Airing Eligibility'

    def lookups(self, request, model_admin):
        return (('yes', 'Currently Eligible'), ('no', 'Not Currently Eligible'))

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.currently_airing()
        elif self.value() == 'no':
            return queryset.not_currently_airing()


class EnabledDatesRotatorMixin:
    list_filter = ('rotators', CurrentlyAiringListFilter, 'enabled')
    actions = ('enable', 'disable')

    def enabled_dates(self, obj, now=None):
        tz = timezone.get_current_timezone()

        enabled_html = '' if obj.currently_airing(now) else '<br><em>Not currently eligible to air.</em>'

        if obj.begin and obj.end:
            return format_html(
                '<b>Begins:</b> {}<br><b>Ends:</b> {}' + enabled_html,
                tz.normalize(obj.begin).strftime(STRFTIME_FMT), tz.normalize(obj.end).strftime(STRFTIME_FMT))
        elif obj.begin:
            return format_html('<b>Begins:</b> {}' + enabled_html,
                               tz.normalize(obj.begin).strftime(STRFTIME_FMT))
        elif obj.end:
            return format_html('<b>Ends:</b> {}' + enabled_html,
                               tz.normalize(obj.end).strftime(STRFTIME_FMT))
        else:
            return 'Always Airs'
    enabled_dates.short_description = 'Air Dates'
    enabled_dates.admin_order_field = Coalesce('begin', 'end')

    def enable(self, request, queryset):
        num = queryset.update(enabled=True)
        if num:
            self.message_user(request, f'Enabled {num} {self.model._meta.verbose_name}(s).', messages.SUCCESS)
    enable.short_description = 'Enable selected %(verbose_name_plural)s'

    def disable(self, request, queryset):
        num = queryset.update(enabled=False)
        if num:
            self.message_user(request, f'Disabled {num} {self.model._meta.verbose_name}(s).', messages.SUCCESS)
    disable.short_description = 'Disable selected %(verbose_name_plural)s'
    disable.allowed_permissions = enable.allowed_permissions = ('add', 'change', 'delete')


class NumAssetsMixin:
    def num_assets(self, obj):
        if isinstance(obj, StopSet):
            filter_kwargs = {'rotators__in': obj.rotators.all()}
        else:
            filter_kwargs = {'rotators': obj}

        num_enabled = Asset.objects.filter(**filter_kwargs).distinct().currently_enabled().count()
        num_disabled = Asset.objects.filter(**filter_kwargs).distinct().count() - num_enabled

        if num_enabled == num_disabled == 0:
            html = '<em>None</em>'
        else:
            html = f'{num_enabled} Airing'
            if num_disabled > 0:
                html = (f'{num_enabled + num_disabled} Total<br><em>'
                        f'({html} / {num_disabled} Not Currently Airing)</em>')
        return mark_safe(html)
    num_assets.short_description = 'Total Audio Assets'


class AssetActionForm(ActionForm):
    rotator = forms.ModelChoiceField(Rotator.objects.all(), required=False,
                                     label=' ', empty_label='--- Rotator ---')


class AssetUploadForm(forms.Form):
    audios = forms.FileField(
        widget=forms.FileInput(attrs={'multiple': True}), required=True, label='Audio Files',
        help_text='Select multiple audio files to upload using Shift, CMD, and/or Alt in the dialog.')
    rotators = forms.ModelMultipleChoiceField(
        Rotator.objects.all(), required=False, widget=forms.CheckboxSelectMultiple(),
        label='Rotators', help_text='Optionally select Rotator(s) to add Audio Assets to.')


class AssetModelAdmin(EnabledDatesRotatorMixin, TomatoModelAdmin):
    action_form = AssetActionForm
    actions = ('enable', 'disable', 'add_rotator', 'remove_rotator')
    filter_horizontal = ('rotators',)
    list_display = ('name', 'rotator_list', 'enabled_dates', 'enabled', 'weight',
                    'duration_pretty', 'audio_player_list')
    list_prefetch_related = 'rotators'
    ordering = ('name',)
    readonly_fields = ('duration_pretty', 'audio_player', 'rotator_list')

    def get_urls(self):
        return [path('upload/', self.admin_site.admin_view(self.upload_view),
                name='tomato_asset_upload')] + super().get_urls()

    def upload_view(self, request):
        if not self.has_add_permission(request):
            raise PermissionDenied

        if request.method == 'POST':
            form = AssetUploadForm(request.POST, request.FILES)
            if form.is_valid():
                audio_files = request.FILES.getlist('audios')
                rotators = form.cleaned_data['rotators']
                assets = []

                for audio in audio_files:
                    asset = Asset(audio=audio)
                    assets.append(asset)

                    try:
                        asset.clean()
                    except forms.ValidationError as validation_error:
                        for field, error_list in validation_error:
                            for error in error_list:
                                form.add_error('audios' if field == 'audio' else '__all__', error)

            # If no errors where added
            if form.is_valid():
                for asset in assets:
                    asset.save()

                    if rotators:
                        asset.rotators.add(*rotators)

                self.message_user(
                    request, f'Uploaded {len(assets)} Audio Assets.', messages.SUCCESS)

                return HttpResponseRedirect(reverse('admin:tomato_asset_changelist'))
        else:
            form = AssetUploadForm()

        opts = self.model._meta
        return TemplateResponse(request, 'admin/tomato/asset/upload.html', {
            'adminform': AdminForm(form, [(None, {'fields': form.base_fields})],
                                   self.get_prepopulated_fields(request)),
            'app_label': opts.app_label,
            'errors': form.errors.values(),
            'form': form,
            'opts': opts,
            'save_on_top': self.save_on_top,
            'title': f'Bulk Upload Audio Assets',
            **self.admin_site.each_context(request),
        })

    def add_rotator(self, request, queryset):
        rotator_id = request.POST.get('rotator')
        if rotator_id:
            rotator = Rotator.objects.get(id=rotator_id)
            for asset in queryset:
                asset.rotators.add(rotator)
            self.message_user(
                request, f'Added {len(queryset)} Audio Asset(s) to {rotator.name}.', messages.SUCCESS)
        else:
            self.message_user(
                request, 'You must select a Rotator to add Audio Asset(s) to.', messages.WARNING)
    add_rotator.short_description = 'Add selected Audio Assets to Rotator'

    def remove_rotator(self, request, queryset):
        rotator_id = request.POST.get('rotator')
        if rotator_id:
            rotator = Rotator.objects.get(id=rotator_id)
            for asset in queryset:
                asset.rotators.remove(rotator)
            self.message_user(
                request, f'Removed {len(queryset)} Audio Asset(s) from {rotator.name}.', messages.SUCCESS)
        else:
            self.message_user(
                request, 'You must select a Rotator to remove Audio Asset(s) from.', messages.WARNING)
    remove_rotator.short_description = 'Remove selected Audio Assets from Rotator'
    remove_rotator.allowed_permissions = add_rotator.allowed_permissions = ('add', 'change', 'delete')

    def get_form(self, request, obj, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'rotators' in form.base_fields:
            form.base_fields['rotators'].widget.can_add_related = False
        return form

    def get_fieldsets(self, request, obj):
        return ((None, {'fields': ('name',) + (('audio_player',) if obj else ()) + ('audio',)}),
                ('Eligibility', {'fields': ('weight', 'enabled', 'begin', 'end')}),
                ('Rotators', {'fields': ('rotators',)}))

    def rotator_list(self, obj):
        rotators = list(obj.rotators.all())
        if rotators:
            html = '<br>'.join(
                (f'&bull; <span style="background-color: #{dict(COLORS)[f"{rotator.color}-light"]}">'
                 f'{escape(rotator.name)}</span>')
                for rotator in rotators)
        else:
            html = '<em>None</em>'
        return mark_safe(html)
    rotator_list.short_description = 'Rotators'

    def duration_pretty(self, obj):
        if obj.duration == datetime.timedelta(seconds=0):
            return 'Unknown'
        seconds = int(obj.duration.total_seconds())
        hours, minutes, seconds = seconds // 3600, (seconds // 60) % 60, seconds % 60
        if hours > 0:
            return '{}:{:02d}:{:02d}'.format(hours, minutes, seconds)
        else:
            return '{}:{:02d}'.format(minutes, seconds)
    duration_pretty.short_description = 'Duration'
    duration_pretty.admin_order_field = 'duration'

    def audio_player(self, obj):
        return format_html('<audio src="{}" style="width: 100%" preload="auto" controls />', obj.audio.url)

    def audio_player_list(self, obj):
        return format_html(
            '<audio src="{}" style="min-width: 250px; width: 100%;" preload="auto" controls />', obj.audio.url)
    audio_player.short_description = audio_player_list.short_description = 'Audio Player'


class StopSetRotatorInline(admin.TabularInline):
    min_num = 1
    extra = 0
    model = StopSetRotator
    verbose_name = 'Rotator Entry'
    verbose_name_plural = 'Rotator Entries'

    def get_formset(self, request, obj, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        widget = formset.form.base_fields['rotator'].widget
        widget.can_add_related = False
        widget.can_change_related = False
        return formset


class GenerateStopSetForm(forms.Form):
    now = forms.SplitDateTimeField(widget=AdminSplitDateTime(), required=False)


class StopSetModelAdmin(EnabledDatesRotatorMixin, NumAssetsMixin, TomatoModelAdmin):
    inlines = (StopSetRotatorInline,)
    list_display = ('name', 'rotator_entry_list', 'enabled_dates', 'enabled',
                    'weight', 'num_assets', 'generate')
    readonly_fields = ('generate',)

    def get_urls(self):
        return [path('<int:object_id>/generate/', self.admin_site.admin_view(self.generate_view),
                name='tomato_stopset_generate')] + super().get_urls()

    def get_fieldsets(self, request, obj):
        return ((None, {'fields': ('name',) + (('generate',) if obj else ())}),
                ('Eligibility', {'fields': ('weight', 'enabled', 'begin', 'end')}))

    def generate_view(self, request, object_id):
        if not self.has_view_permission(request):
            raise PermissionDenied

        now = timezone.localtime()

        if request.method == 'POST':
            form = GenerateStopSetForm(request.POST)
            if form.is_valid() and form.cleaned_data['now']:
                now = form.cleaned_data['now']

        else:
            form = GenerateStopSetForm()

        stopset = get_object_or_404(StopSet, id=object_id)

        opts = self.model._meta
        return TemplateResponse(request, 'admin/tomato/stopset/generate.html', {
            'app_label': opts.app_label,
            'asset_block': stopset.generate_asset_block(now),
            'currently_airing': stopset.currently_airing(now),
            'enabled_dates': self.enabled_dates(stopset, now),
            'now': now.strftime(STRFTIME_FMT),
            'opts': opts,
            'form': form,
            'save_on_top': self.save_on_top,
            'stopset': stopset,
            'timezone': now.tzinfo.zone,
            'title': f'Generate Sample Stop Set Block: {stopset.name}',
            **self.admin_site.each_context(request),
        })

    def rotator_entry_list(self, obj):
        rotator_entries = list(StopSetRotator.objects.filter(stopset=obj).order_by(
            'id').values_list('rotator__name', 'rotator__color'))
        if rotator_entries:
            html = '<br>'.join(
                f'<span style="background-color: #{dict(COLORS)[f"{color}-light"]}">{num}. {escape(name)}</span>'
                for num, (name, color) in enumerate(rotator_entries, 1))
        else:
            html = '<em>None</em>'
        return mark_safe(html)
    rotator_entry_list.short_description = 'Rotator Entries'

    def generate(self, obj):
        return format_html('<a href="{}">Generate Sample Block</a>',
                           reverse('admin:tomato_stopset_generate', args=(obj.id,)))
    generate.short_description = 'Generate Sample Block'


class RotatorModelAdmin(NumAssetsMixin, TomatoModelAdmin):
    readonly_fields = ('display_color', 'stopset_list', 'num_assets')
    list_display = ('name', 'stopset_list', 'display_color', 'num_assets')
    list_filter = ('stopsets',)
    list_prefetch_related = 'stopsets'

    class Media:
        js = ('admin/js/rotator_color.js',)

    def get_fields(self, request, obj):
        return ('name', 'color', 'display_color') + (('stopset_list', 'num_assets') if obj else ())

    def display_color(self, obj):
        return format_html('<div class="color-preview" style="width: 8em; height: 3em; '
                           'border: 1px solid #333; display: inline-block;{}"></div>',
                           f' background-color: #{dict(COLORS)[obj.color]}' if isinstance(obj, Rotator) else '')
    display_color.short_description = 'Display Color'

    def stopset_list(self, obj):
        # De-dupe in Python rather than in queryset, to leverage list_prefetch_related
        stopsets = sorted(set(obj.stopsets.all()), key=lambda ss: ss.name)
        if stopsets:
            html = '<br>'.join(f'&bull; {escape(stopset.name)}' for stopset in stopsets)
        else:
            html = '<em>None</em>'
        return mark_safe(html)
    stopset_list.short_description = 'Stop Sets'


admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(User, TomatoUserAdmin)
admin.site.register(StopSet, StopSetModelAdmin)
admin.site.register(Rotator, RotatorModelAdmin)
admin.site.register(Asset, AssetModelAdmin)
