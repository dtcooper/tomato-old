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

from data.models import Asset, Rotator, RotatorAsset, StopSet, StopSetRotator


class TomatoUserAdmin(UserAdmin):
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


class ModelAdmin(admin.ModelAdmin):
    save_on_top = True
    list_per_page = 250
    search_fields = ('name',)


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


class RotatorInlineBase(admin.TabularInline):
    def get_formset(self, request, obj, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        widget = formset.form.base_fields['rotator'].widget
        widget.can_add_related = False
        widget.can_change_related = False
        return formset


class StopSetRotatorInline(RotatorInlineBase):
    min_num = 1
    extra = 0
    model = StopSetRotator
    verbose_name = 'Rotator Entry'
    verbose_name_plural = 'Rotator Entries'


class StopSetModelAdmin(EnabledBeginEndMixin, NumAssetsMixin, ModelAdmin):
    inlines = (StopSetRotatorInline,)
    readonly_fields = ('is_currently_enabled_reason',)
    list_display = ('name', 'rotator_entry_list', 'is_currently_enabled',
                    'enabled_dates', 'weight', 'num_assets')

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


class RotatorModelAdmin(NumAssetsMixin, ModelAdmin):
    readonly_fields = ('display_color',)
    list_display = ('name', 'stopset_list', 'display_color', 'num_assets')

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


class RotatorAssetInline(RotatorInlineBase):
    model = RotatorAsset
    extra = 1
    ordering = ('rotator__name',)
    verbose_name = 'Rotator'
    verbose_name_plural = 'Rotator'


class AssetActionForm(ActionForm):
    rotator = forms.ModelChoiceField(Rotator.objects.all(), required=False,
                                     label=' ', empty_label='----- Rotator -----')


class AssetUploadForm(forms.Form):
    audio_files = forms.FileField(
        widget=forms.FileInput(attrs={'multiple': True}), required=True, label='Audio Files',
        help_text='Select multiple audio files to upload using Shift, CMD, and/or Alt in the dialog.')
    rotators = forms.ModelMultipleChoiceField(
        Rotator.objects.all(), required=False, widget=forms.CheckboxSelectMultiple(),
        label='Rotators', help_text='Select Rotators to add Audio Assets to.')


class AssetModelAdmin(EnabledBeginEndMixin, ModelAdmin):
    action_form = AssetActionForm
    inlines = (RotatorAssetInline,)
    list_display = ('view_name', 'rotator_list', 'is_currently_enabled',
                    'enabled_dates', 'weight', 'list_audio_player')
    readonly_fields = ('audio_player', 'is_currently_enabled_reason', 'rotator_list')
    ordering = ('name',)
    actions = ('add_rotator', 'remove_rotator')
    list_filter = ('rotators__name',)  # TODO: allow for rotator = None here

    def get_urls(self):
        return [
            path('upload/', self.admin_site.admin_view(self.upload), name='data_asset_upload')
        ] + super().get_urls()

    def upload(self, request):
        if not self.has_add_permission(request):
            raise PermissionDenied

        if request.method == 'POST':
            form = AssetUploadForm(request.POST, request.FILES)
            if form.is_valid():
                audio_files = request.FILES.getlist('audio_files')
                rotators = list(form.cleaned_data.get('rotators', []))

                for audio in audio_files:
                    asset = Asset(audio=audio)
                    asset.save()

                    if rotators:
                        asset.rotators.add(*rotators)

                self.message_user(
                    request, f'Uploaded {len(audio_files)} assets.', messages.SUCCESS)

                return HttpResponseRedirect(reverse('admin:data_asset_changelist'))
        else:
            form = AssetUploadForm()

        opts = self.model._meta
        context = self.admin_site.each_context(request)
        context.update({
            'opts': opts,
            'app_label': opts.app_label,
            'title': f'Bulk Upload {opts.verbose_name_plural.title()}',
            'form': form,

            'adminform': AdminForm(form, [(None, {'fields': form.base_fields})],
                                   self.get_prepopulated_fields(request))
        })
        return TemplateResponse(request, 'admin/data/asset/upload.html', context)

    def add_rotator(self, request, queryset):
        rotator_id = request.POST.get('rotator')
        if rotator_id:
            rotator = Rotator.objects.get(id=rotator_id)
            num_added = 0
            for asset in queryset:
                rotator_asset = RotatorAsset(asset=asset, rotator=rotator)
                if rotator_asset.save():
                    num_added += 1

            self.message_user(
                request, f'Added {num_added} asset(s) to {rotator.name}.', messages.SUCCESS)
        else:
            self.message_user(
                request, 'You must select a Rotator to add asset(s) to.', messages.WARNING)
    add_rotator.short_description = 'Add selected to Rotator'

    def remove_rotator(self, request, queryset):
        rotator_id = request.POST.get('rotator')
        if rotator_id:
            rotator = Rotator.objects.get(id=rotator_id)
            num_deleted, _ = RotatorAsset.objects.filter(asset__in=queryset, rotator=rotator).delete()
            self.message_user(
                request, f'Removed {num_deleted} asset(s) from {rotator.name}.', messages.SUCCESS)
        else:
            self.message_user(
                request, 'You must select a Rotator to remove asset(s) from.', messages.WARNING)
    remove_rotator.short_description = 'Remove selected from Rotator'
    add_rotator.allowed_permissions = remove_rotator.allowed_permissions = ('add', 'change', 'delete')

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

    def list_audio_player(self, obj):
        return format_html('<audio src="{}" style="width: 250px" preload="auto" controls />',
                           obj.audio.url)
    list_audio_player.short_description = audio_player.short_description = 'Audio Player'


admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(User, TomatoUserAdmin)
admin.site.register(StopSet, StopSetModelAdmin)
admin.site.register(Rotator, RotatorModelAdmin)
admin.site.register(Asset, AssetModelAdmin)
