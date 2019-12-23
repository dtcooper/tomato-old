from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ActionForm, AdminForm
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.db.models.functions import Coalesce
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import escape, format_html, mark_safe

from data.models import Asset, Rotator, StopSet, StopSetRotator


class TomatoUserAdmin(UserAdmin):
    save_on_top = True
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_superuser', 'groups',)}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_superuser')
    list_filter = ('is_superuser', 'is_active', 'groups')

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.exclude(username='anonymous_superuser')

    def save_model(self, request, obj, form, change):
        obj.is_staff = True
        return super().save_model(request, obj, form, change)

    def has_module_permission(self, request):
        has_perm = super().has_module_permission(request)
        return has_perm and request.user.username != 'anonymous_superuser'


class TomatoModelAdmin(admin.ModelAdmin):
    save_on_top = True
    list_per_page = 250
    search_fields = ('name',)
    empty_value_display = 'None'


class CurrentlyAiringListFilter(admin.SimpleListFilter):
    title = 'Airing Eligibility'
    parameter_name = 'airing'

    def lookups(self, request, model_admin):
        return (('yes', 'Currently Eligible'), ('no', 'Not Currently Eligible'))

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.currently_airing()
        elif self.value() == 'no':
            return queryset.not_currently_airing()


class EnabledDatesRotatorMixin:
    list_filter = ('rotators', CurrentlyAiringListFilter, 'enabled')

    def enabled_dates(self, obj):
        tz = timezone.get_default_timezone()
        fmt = '%a %b %-d %Y %-I:%M %p'

        enabled_html = '' if obj.currently_airing() else '<br><em>Not currently eligible to air.</em>'

        if obj.begin and obj.end:
            return format_html(
                '<b>Begins:</b> {}<br><b>Ends:</b> {}' + enabled_html,
                tz.normalize(obj.begin).strftime(fmt), tz.normalize(obj.end).strftime(fmt))
        elif obj.begin:
            return format_html('<b>Begins:</b> {}' + enabled_html,
                               tz.normalize(obj.begin).strftime(fmt))
        elif obj.end:
            return format_html('<b>Ends:</b> {}' + enabled_html,
                               tz.normalize(obj.end).strftime(fmt))
        else:
            return 'Always Airs'
    enabled_dates.short_description = 'Air Dates'
    enabled_dates.admin_order_field = Coalesce('begin', 'end')

    def enable(self, request, queryset):
        queryset.update(enabled=True)
    enable.short_description = 'Enable selected %(verbose_name_plural)s'

    def disable(self, request, queryset):
        queryset.update(enabled=False)
    disable.short_description = 'Disable selected %(verbose_name_plural)s'
    disable.allowed_permissions = enable.allowed_permissions = ('add', 'change', 'delete')


class NumAssetsMixin:
    def num_assets(self, obj):
        if isinstance(obj, StopSet):
            filter_kwargs = {'rotators__in': obj.rotators.all()}
        else:
            filter_kwargs = {'rotators': obj}

        num_enabled = Asset.objects.filter(**filter_kwargs).currently_enabled().count()
        num_disabled = Asset.objects.filter(**filter_kwargs).count() - num_enabled

        if num_enabled == num_disabled == 0:
            html = '<em>None</em>'
        else:
            html = f'{num_enabled} Airing'
            if num_disabled > 0:
                html = (f'{num_enabled + num_disabled} Total<br><em>'
                        f'({html} / {num_disabled} Not Currently Airing)</em>')
        return mark_safe(html)
    num_assets.short_description = 'Total Audio Assets'


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


class StopSetModelAdmin(EnabledDatesRotatorMixin, NumAssetsMixin, TomatoModelAdmin):
    inlines = (StopSetRotatorInline,)
    list_display = ('name', 'rotator_entry_list', 'enabled', 'enabled_dates', 'weight', 'num_assets')
    fieldsets = ((None, {'fields': ('name',)}),
                 ('Eligibility', {'fields': ('weight', 'enabled', 'begin', 'end')}))

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


class RotatorModelAdmin(NumAssetsMixin, TomatoModelAdmin):
    readonly_fields = ('display_color',)
    list_display = ('name', 'stopset_list', 'display_color', 'num_assets')
    list_filter = ('stopsets',)

    def display_color(self, obj):
        return format_html('<div class="color-preview" style="width: 8em; height: 3em; '
                           'border: 1px solid #333; display: inline-block;{}"></div>',
                           f' background-color: #{obj.color}' if isinstance(obj, Rotator) else '')
    display_color.short_description = 'Display Color'

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

    class Media:
        js = ('admin/js/rotator_color.js',)


class AssetActionForm(ActionForm):
    rotator = forms.ModelChoiceField(Rotator.objects.all(), required=False,
                                     label=' ', empty_label='--- Rotator ---')


class AssetUploadForm(forms.Form):
    audio_files = forms.FileField(
        widget=forms.FileInput(attrs={'multiple': True}), required=True, label='Audio Files',
        help_text='Select multiple audio files to upload using Shift, CMD, and/or Alt in the dialog.')
    rotators = forms.ModelMultipleChoiceField(
        Rotator.objects.all(), required=False, widget=forms.CheckboxSelectMultiple(),
        label='Rotators', help_text='Optionally select Rotator(s) to add Audio Assets to.')


class AssetModelAdmin(EnabledDatesRotatorMixin, TomatoModelAdmin):
    action_form = AssetActionForm
    list_display = ('name', 'list_rotators', 'enabled', 'enabled_dates', 'weight', 'list_audio_player')
    readonly_fields = ('audio_player', 'list_rotators')
    ordering = ('name',)
    actions = ('enable', 'disable', 'add_rotator', 'remove_rotator')
    filter_horizontal = ('rotators',)

    def get_urls(self):
        return [path('upload/', self.admin_site.admin_view(self.upload),
                name='data_asset_upload')] + super().get_urls()

    def upload(self, request):
        if not self.has_add_permission(request):
            raise PermissionDenied

        if request.method == 'POST':
            form = AssetUploadForm(request.POST, request.FILES)
            if form.is_valid():
                audio_files = request.FILES.getlist('audio_files')
                rotators = form.cleaned_data['rotators']

                for audio in audio_files:
                    asset = Asset(audio=audio)
                    asset.save()

                    if rotators:
                        asset.rotators.add(*rotators)

                self.message_user(
                    request, f'Uploaded {len(audio_files)} Audio Assets.', messages.SUCCESS)

                return HttpResponseRedirect(reverse('admin:data_asset_changelist'))
        else:
            form = AssetUploadForm()

        opts = self.model._meta
        context = self.admin_site.each_context(request)
        context.update({
            'opts': opts,
            'app_label': opts.app_label,
            'title': f'Bulk Upload Audio Assets',
            'form': form,
            'save_on_top': self.save_on_top,
            'adminform': AdminForm(form, [(None, {'fields': form.base_fields})],
                                   self.get_prepopulated_fields(request))
        })
        return TemplateResponse(request, 'admin/data/asset/upload.html', context)

    def add_rotator(self, request, queryset):
        rotator_id = request.POST.get('rotator')
        if rotator_id:
            rotator, num_added = Rotator.objects.get(id=rotator_id), 0
            num_added = 0
            for asset in queryset:
                num_before = asset.rotators.count()
                asset.rotators.add(rotator)
                num_added += asset.rotators.count() - num_before
            self.message_user(
                request, f'Added {num_added} asset(s) to {rotator.name}.', messages.SUCCESS)
        else:
            self.message_user(
                request, 'You must select a Rotator to add Audio Asset(s) to.', messages.WARNING)
    add_rotator.short_description = 'Add selected Audio Assets to Rotator'

    def remove_rotator(self, request, queryset):
        rotator_id = request.POST.get('rotator')
        if rotator_id:
            rotator, num_deleted = Rotator.objects.get(id=rotator_id), 0
            for asset in queryset:
                num_before = asset.rotators.count()
                asset.rotators.remove(rotator)
                num_deleted += num_before - asset.rotators.count()
            self.message_user(
                request, f'Removed {num_deleted} asset(s) from {rotator.name}.', messages.SUCCESS)
        else:
            self.message_user(
                request, 'You must select a Rotator to remove Audio Asset(s) from.', messages.WARNING)
    remove_rotator.short_description = 'Remove selected Audio Assets from Rotator'
    remove_rotator.allowed_permissions = add_rotator.allowed_permissions = ('add', 'change', 'delete')

    def get_form(self, request, obj, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['rotators'].widget.can_add_related = False
        return form

    def get_fieldsets(self, request, obj):
        return ((None, {'fields': ('name',) + (('audio_player',) if obj else ()) + ('audio',)}),
                ('Eligibility', {'fields': ('weight', 'enabled', 'begin', 'end')}),
                ('Rotators', {'fields': ('rotators',)}))

    def list_rotators(self, obj):
        rotators = list(obj.rotators.order_by('name').values_list('name', 'color'))
        if rotators:
            html = '<br>'.join(
                f'&bull; <span style="background-color: #{color}">{escape(name)}</span>'
                for name, color in rotators)
        else:
            html = '<em>None</em>'
        return mark_safe(html)
    list_rotators.short_description = 'Rotators'

    def __audio_player(size):
        def player(self, obj):
            html = '<audio src="{}" style="width: {};" preload="auto" controls />'
            return format_html(html, obj.audio.url, size)
        player.short_description = 'Audio Player'
        return player
    audio_player = __audio_player('100%')
    list_audio_player = __audio_player('250px')


admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(User, TomatoUserAdmin)
admin.site.register(StopSet, StopSetModelAdmin)
admin.site.register(Rotator, RotatorModelAdmin)
admin.site.register(Asset, AssetModelAdmin)
