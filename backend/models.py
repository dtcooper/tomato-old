from functools import partial
import hashlib
import os

from django.conf import settings
from django.db import models
from django.utils import timezone


class CurrentlyEnabledQueryset(models.QuerySet):
    def currently_enabled(self):
        now = timezone.now()
        return self.filter(
            models.Q(enabled=True)
            & (models.Q(begin__isnull=True) | models.Q(begin__lt=now))
            & (models.Q(end__isnull=True) | models.Q(end__gt=now))
        )


class EnabledBeginEndWeightMixin(models.Model):
    objects = CurrentlyEnabledQueryset.as_manager()

    enabled = models.BooleanField(
        'Enabled', default=True,
        help_text=('If this is checked, enabled to be randomly selected. If unchecked '
                   'random selection is disabled, regardless of begin and end air date below.'))
    begin = models.DateTimeField(
        'Begin Air Date', null=True, blank=True,
        help_text=('Optional date when eligibility for random selection *begins*. If specified, '
                   f'random selection is enabled after this date. (Timezone: {settings.TIME_ZONE})'))
    end = models.DateTimeField(
        'End Air Date', null=True, blank=True,
        help_text=('Optional date when eligibility for random selection *ends*. If specified, '
                   f'random selection is enabled before this date. (Timezone: {settings.TIME_ZONE})'))
    weight = models.PositiveSmallIntegerField(
        'Random Weight', default=1,
        help_text=('The weight (ie selection bias) for how likely random '
                   "selection occurs, eg '1' is just as likely as all others, "
                   " '2' is 2x as likely, '3' is 3x as likely and so on."))

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


class Rotator(models.Model):
    COLOR_CHOICES = (
        # accent-1 choices from https://materializecss.com/color.html
        ('ff8a80', 'Red'), ('ff80ab', 'Pink'), ('ea80fc', 'Purple'), ('b388ff', 'Deep Purple'),
        ('8c9eff', 'Indigo'), ('82b1ff', 'Blue'), ('80d8ff', 'Light Blue'), ('84ffff', 'Cyan'),
        ('a7ffeb', 'Teal'), ('b9f6ca', 'Green'), ('ccff90', 'Light Green'), ('f4ff81', 'Lime'),
        ('ffff8d', 'Yellow'), ('ffe57f', 'Amber'), ('ffd180', 'Orange'), ('ff9e80', 'Deep Orange'),
    )

    name = models.CharField(
        'Rotator Name', max_length=50, db_index=True,
        help_text=("Category name of this asset rotator, eg 'ADs', 'Station IDs, "
                   "'Short Interviews', etc."))
    color = models.CharField(
        'Color', default=COLOR_CHOICES[0][0], max_length=6,
        choices=COLOR_CHOICES,
        help_text='Color that appears in the playout software for assets in this rotator.')
    stopsets = models.ManyToManyField(
        StopSet,
        through='StopSetRotator',
        through_fields=('rotator', 'stopset'),
        related_name='rotators')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'rotators'
        verbose_name = 'Rotator'
        verbose_name_plural = 'Rotators'
        ordering = ('name',)


class StopSetRotator(models.Model):
    stopset = models.ForeignKey(StopSet, on_delete=models.CASCADE, null=False)
    rotator = models.ForeignKey(
        Rotator, on_delete=models.CASCADE, null=False, verbose_name='Rotator')

    def __str__(self):
        return self.rotator.name

    class Meta:
        db_table = 'stopset_entries'
        verbose_name = 'Rotator Entry'
        verbose_name_plural = 'Rotator Entries'
        ordering = ('id',)


class Asset(EnabledBeginEndWeightMixin, models.Model):
    name = models.CharField('Optional Name', max_length=50, blank=True, db_index=True)
    md5sum = models.CharField(max_length=32)
    audio = models.FileField('Audio File', upload_to='assets/')
    rotators = models.ManyToManyField(
        Rotator,
        through='RotatorAsset',
        through_fields=('asset', 'rotator'),
        related_name='assets')

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


class RotatorAsset(models.Model):
    rotator = models.ForeignKey(
        Rotator, on_delete=models.CASCADE, null=False, verbose_name='Rotator')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, null=False)
    # TODO: length?

    def save(self, *args, **kwargs):
        # Enforce uniqueness
        if not RotatorAsset.objects.filter(rotator=self.rotator,
                                           asset=self.asset).exists():
            super().save(*args, **kwargs)

    def __str__(self):
        return self.rotator.name

    class Meta:
        db_table = 'rotator_entries'
        verbose_name = 'Rotator'
        verbose_name_plural = 'Rotators'
        ordering = ('id',)
