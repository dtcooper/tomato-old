from functools import partial
import hashlib
import os

from django.conf import settings
from django.db import models
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.html import format_html


class EnabledBeginEndWeightMixin(models.Model):
    enabled = models.BooleanField(
        'Enabled', default=True,
        help_text=('If this is checked, enabled to be randomly selected. If unchecked '
                   'random selection is disabled, regardless of begin and end air date below.'))
    begin = models.DateTimeField(
        'Begin Air Date', null=True, blank=True,
        help_text=('Optional date when eligibility for random selection *begins*. If specified, '
                   f'random selection is disabled after this date. (Timezone: {settings.TIME_ZONE})'))
    end = models.DateTimeField(
        'End Air Date', null=True, blank=True,
        help_text=('Optional date when eligibility for random selection *ends*. If specified, '
                   f'random selection is disabled after this date. (Timezone: {settings.TIME_ZONE})'))
    weight = models.PositiveSmallIntegerField(
        'Random Weight', default=1,
        help_text=('The weight (ie selection bias) for how likely random '
                   "selection occurs, eg '1' is just as likely as all others, "
                   " '2' is 2x as likely, '3' is 3x as likely and so on."))

    def is_currently_enabled(self):
        now = timezone.now()
        return (self.enabled and (self.begin is None or self.begin < now)
                and (self.end is None or self.end > now))
    is_currently_enabled.boolean = True
    is_currently_enabled.short_description = 'Currently Enabled?'
    # TODO: annotate queryset in model admin with new field, then order by that

    def is_currently_enabled_reason(self):
        reasons = []
        if not self.enabled:
            reasons.append('via checkbox')

        now = timezone.now()
        if self.begin is not None and now < self.begin:
            reasons.append('Begin Date in the future')
        if self.end is not None and now > self.end:
            reasons.append('End Date in the past')

        return f'Disabled: {", ".join(reasons)}' if reasons else 'Enabled'
    is_currently_enabled_reason.short_description = 'Currently Enabled?'

    def enabled_dates(self):
        tz = timezone.get_default_timezone()
        fmt = '%a %b %-d %Y %-I:%M %p'

        if self.begin and self.end:
            return '{} to {}'.format(
                tz.normalize(self.begin).strftime(fmt),
                tz.normalize(self.end).strftime(fmt))
        elif self.begin:
            return format_html(
                '<b>Begins</b> {}', tz.normalize(self.begin).strftime(fmt))
        elif self.end:
            return format_html(
                '<b>Ends</b> {}', tz.normalize(self.end).strftime(fmt))
        else:
            return 'Always'
    enabled_dates.short_description = 'Air Dates'
    enabled_dates.admin_order_field = Coalesce('begin', 'end')

    def save(self, *args, **kwargs):
        if self.weight <= 0:
            self.weight = 1
        return super().save(*args, **kwargs)

    class Meta:
        abstract = True


class StopSet(EnabledBeginEndWeightMixin, models.Model):
    name = models.CharField('Name', max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'stopsets'
        verbose_name = 'Stop Set'
        verbose_name_plural = 'Stop Sets'


class Rotation(models.Model):
    name = models.CharField(
        'Rotation Name', max_length=50, db_index=True,
        help_text=("Category name of this asset rotation, eg 'ADs', 'Station IDs, "
                   "'Short Interviews', etc."))
    color = models.CharField(
        'Color', default='80d8ff', max_length=6,
        choices=(
            # accent-1 choices from https://materializecss.com/color.html
            ('ff8a80', 'Red'), ('ff80ab', 'Pink'), ('ea80fc', 'Purple'),
            ('b388ff', 'Deep Purple'), ('8c9eff', 'Indigo'), ('82b1ff', 'Blue'),
            ('80d8ff', 'Light Blue'), ('84ffff', 'Cyan'), ('a7ffeb', 'Teal'),
            ('b9f6ca', 'Green'), ('ccff90', 'Light Green'), ('f4ff81', 'Lime'),
            ('ffff8d', 'Yellow'), ('ffe57f', 'Amber'), ('ffd180', 'Orange'),
            ('ff9e80', 'Deep Orange'),
        ),
        help_text='Color that appears in the desktop software for assets in this rotation.')
    stopsets = models.ManyToManyField(
        StopSet,
        through='StopSetRotation',
        through_fields=('rotation', 'stopset'))

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'rotations'
        verbose_name = 'Rotation'
        verbose_name_plural = 'Rotations'
        ordering = ('name',)


class StopSetRotation(models.Model):
    stopset = models.ForeignKey(StopSet, on_delete=models.CASCADE, null=False)
    rotation = models.ForeignKey(
        Rotation, on_delete=models.CASCADE, null=False, verbose_name='Rotation')

    def __str__(self):
        return self.rotation.name

    class Meta:
        db_table = 'stopset_entries'
        verbose_name = 'Rotation Entry'
        verbose_name_plural = 'Rotation Entries'
        ordering = ('id',)


class Asset(EnabledBeginEndWeightMixin, models.Model):
    name = models.CharField('Optional Name', max_length=50, blank=True, db_index=True)
    md5sum = models.CharField(max_length=32)
    audio = models.FileField('Audio File', upload_to='assets/')
    rotations = models.ManyToManyField(
        Rotation,
        through='RotationAsset',
        through_fields=('asset', 'rotation'))

    def save(self, *args, **kwargs):
        # Hash in 64kb chunks
        md5_hasher = hashlib.md5()
        for data_chunk in iter(partial(self.audio.read, 64 * 1024), b''):
            md5_hasher.update(data_chunk)
        self.md5sum = md5_hasher.hexdigest()

        # Give asset a name based on filename
        if not self.name.strip():
            self.name = os.path.splitext(os.path.basename(self.audio.name))[0]

        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'assets'
        verbose_name = 'Audio Asset'
        verbose_name_plural = 'Audio Assets'
        ordering = ('name', 'id')


class RotationAsset(models.Model):
    rotation = models.ForeignKey(
        Rotation, on_delete=models.CASCADE, null=False, verbose_name='Rotation')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, null=False)
    # TODO: length?

    def save(self, *args, **kwargs):
        # Enforce uniqueness
        if not RotationAsset.objects.filter(rotation=self.rotation,
                                            asset=self.asset).exists():
            super().save(*args, **kwargs)

    def __str__(self):
        return self.rotation.name

    class Meta:
        db_table = 'rotation_entries'
        verbose_name = 'Rotation'
        verbose_name_plural = 'Rotations'
        ordering = ('id',)
