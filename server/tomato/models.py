import datetime
from functools import partial
import hashlib
import os

import sox

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.db import models
from django.utils import timezone


MAX_NAME_LEN = 100


class CurrentlyEnabledQueryset(models.QuerySet):
    def currently_airing(self):
        now = timezone.now()
        return self.filter((models.Q(begin__isnull=True) | models.Q(begin__lte=now))
                           & (models.Q(end__isnull=True) | models.Q(end__gte=now)))

    def not_currently_airing(self):
        now = timezone.now()
        return self.exclude((models.Q(begin__isnull=True) | models.Q(begin__lte=now))
                            & (models.Q(end__isnull=True) | models.Q(end__gte=now)))

    def currently_enabled(self):
        return self.filter(enabled=True).currently_airing()


class EnabledBeginEndWeightMixin(models.Model):
    objects = CurrentlyEnabledQueryset.as_manager()

    enabled = models.BooleanField(
        'Enabled', default=True,
        help_text=('If this is checked, enabled to be randomly selected. If unchecked '
                   'random selection is disabled, regardless of begin and end air date below.'))
    begin = models.DateTimeField(
        'Begin Air Date', null=True, blank=True,
        help_text=('Optional date when eligibility for random selection *begins*. '
                   'If specified, random selection is eligible after this date.'))
    end = models.DateTimeField(
        'End Air Date', null=True, blank=True,
        help_text=('Optional date when eligibility for random selection *ends*. '
                   'If specified, random selection is eligible before this date.'))
    weight = models.DecimalField(
        'Random Weight', max_digits=5, decimal_places=2, default=1,
        help_text=('The weight (ie selection bias) for how likely random '
                   "selection occurs, eg '1' is just as likely as all others, "
                   "'2' is 2x as likely, '3' is 3x as likely, '0.5' half as likely, "
                   'and so on.'))

    def currently_airing(self):
        now = timezone.now()
        if self.begin and self.end:
            return self.begin <= now <= self.end
        elif self.begin:
            return self.begin <= now
        elif self.end:
            return self.end >= now
        else:
            return True

    def save(self, *args, **kwargs):
        if self.weight <= 0:
            self.weight = 1
        return super().save(*args, **kwargs)

    class Meta:
        abstract = True


class StopSet(EnabledBeginEndWeightMixin, models.Model):
    name = models.CharField('Name', max_length=MAX_NAME_LEN)

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
        'Rotator Name', max_length=MAX_NAME_LEN, db_index=True,
        help_text="Category name of this asset rotator, eg 'ADs', 'Station IDs, 'Short Interviews', etc.")
    color = models.CharField(
        'Color', default=COLOR_CHOICES[0][0], max_length=6, choices=COLOR_CHOICES,
        help_text='Color that appears in the playout software for assets in this rotator.')
    stopsets = models.ManyToManyField(StopSet, through='StopSetRotator', related_name='rotators',
                                      through_fields=('rotator', 'stopset'), verbose_name='Stop Set')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'rotators'
        verbose_name = 'Rotator'
        verbose_name_plural = 'Rotators'
        ordering = ('name',)


class StopSetRotator(models.Model):
    stopset = models.ForeignKey(StopSet, on_delete=models.CASCADE)
    rotator = models.ForeignKey(Rotator, on_delete=models.CASCADE, verbose_name='Rotator')

    def __str__(self):
        s = f'{self.rotator.name} in {self.stopset.name}'
        if self.id:
            num = StopSetRotator.objects.filter(stopset=self.stopset, id__lte=self.id).count()
            s = f'{num}. {s}'
        return s

    class Meta:
        db_table = 'stopset_rotators'
        verbose_name = 'Rotator in Stop Set relationship'
        verbose_name_plural = 'Rotator in Stop Set relationships'
        ordering = ('id',)


class Asset(EnabledBeginEndWeightMixin, models.Model):
    name = models.CharField('Name', max_length=MAX_NAME_LEN, blank=True, db_index=True,
                            help_text="Optional name, if left unspecified, we'll base it off the audio file's "
                                      'metadata, failing that its filename.')
    md5sum = models.CharField(max_length=32)
    duration = models.DurationField()
    audio = models.FileField('Audio File', upload_to='assets/')
    rotators = models.ManyToManyField(Rotator, related_name='assets', blank=True, verbose_name='Rotators',
                                      help_text='Rotators that this asset will be included in.')

    def save(self, *args, **kwargs):
        # Hash in 64kb chunks
        md5_hasher = hashlib.md5()
        for data_chunk in iter(partial(self.audio.read, 64 * 1024), b''):
            md5_hasher.update(data_chunk)
        self.md5sum = md5_hasher.hexdigest()

        # If first save, ie pk is None, action on:
        # - STRIP_UPLOADED_AUDIO
        # - NORMALIZE_AUDIO_TO_MP3
        # - NORMALIZE_AUDIO_TO_MP3_BITRATE

        if not self.name.strip():
            self.name = self.get_default_name()
        self.name = self.name[:MAX_NAME_LEN]
        self.duration = self.get_duration()
        return super().save(*args, **kwargs)

    @property
    def audio_path(self):
        if self.audio:
            if isinstance(self.audio.file, TemporaryUploadedFile):
                return self.audio.file.temporary_file_path()
            else:
                return self.audio.path

    def get_duration(self):
        duration = sox.file_info.duration(self.audio_path)
        return datetime.timedelta(seconds=duration or 0)

    def get_default_name(self, default=None):
        tags = {}
        comments = sox.file_info.comments(self.audio_path)

        for comment in comments.strip().splitlines():
            comment_parts = comment.split('=', 1)
            if len(comment_parts) == 2:
                tags[comment_parts[0].lower()] = comment_parts[1]

        artist, title = tags.get('artist'), tags.get('title')

        if artist and title:
            return f'{artist} - {title}'
        elif title:
            return title
        else:
            return os.path.splitext(os.path.basename(self.audio.name))[0]

    def clean(self):
        if self.audio:
            allowed_file_types = ', '.join(settings.VALID_FILE_TYPES_SOXI_TO_EXTENSIONS.values())
            error_msg = f"Invalid file: '{self.audio.name}'. Valid file types: {allowed_file_types}"

            # check if file valid based on sox
            try:
                file_type = sox.file_info.file_type(self.audio_path)
            except sox.SoxiError:
                raise ValidationError({'audio': error_msg})
            else:
                if file_type not in settings.VALID_FILE_TYPES_SOXI_TO_EXTENSIONS:
                    raise ValidationError({'audio': error_msg})

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'assets'
        verbose_name = 'Audio Asset'
        verbose_name_plural = 'Audio Assets'
        ordering = ('name', 'id')


# For prettier admin display
Asset.rotators.through.__str__ = lambda self: f'{self.asset.name} in {self.rotator.name}'
Asset.rotators.through._meta.verbose_name = 'Asset in Rotator relationship'
Asset.rotators.through._meta.verbose_name_plural = 'Asset in Rotator relationships'
