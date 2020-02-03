import datetime
import os
import random
import subprocess

try:
    import sox
    HAVE_SOX = True
except ImportError:
    HAVE_SOX = False

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

    @classmethod
    def generate_asset_block(cls):
        stopsets = list(cls.objects.currently_enabled().exclude(rotators=None))
        if not stopsets:
            return None, None

        stopset = random.choices(stopsets, weights=[float(s.weight) for s in stopsets], k=1)[0]
        rotators = stopset.get_rotator_block()

        rotator_assets = {
            rotator: list(rotator.assets.currently_enabled())
            # Instantiate one list of assets per rotator
            for rotator in set(rotators)
        }

        asset_block = []
        for rotator in rotators:
            assets = rotator_assets[rotator]
            if assets:
                # Pick a random asset according to its weight
                asset = random.choices(assets, weights=[float(a.weight) for a in assets], k=1)[0]

                # Remove asset from being eligible to play again in this block, even if it's
                # part of another rotator
                for assets in rotator_assets.values():
                    try:
                        assets.remove(asset)
                    except ValueError:
                        pass

            else:
                asset = None

            asset_block.append(asset)

        return stopset, list(zip(rotators, asset_block))

    def get_rotator_block(self):
        return [ssr.rotator for ssr in StopSetRotator.objects.filter(stopset=self).order_by('id')]

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
    duration = models.DurationField()
    audio = models.FileField('Audio File', upload_to='assets/')
    audio_size = models.IntegerField()
    rotators = models.ManyToManyField(Rotator, related_name='assets', blank=True, verbose_name='Rotators',
                                      help_text='Rotators that this asset will be included in.')

    def save(self, *args, **kwargs):
        # If first save, ie pk is None, action on:
        # - STRIP_UPLOADED_AUDIO

        if HAVE_SOX:
            if not self.name.strip():
                self.name = self.get_default_name()
            self.duration = self.get_duration()

        self.name = self.name[:MAX_NAME_LEN]
        self.audio_size = self.audio.file.size

        return super().save(*args, **kwargs)

    @property
    def audio_path(self):
        if self.audio:
            if isinstance(self.audio.file, TemporaryUploadedFile):
                return self.audio.file.temporary_file_path()
            else:
                return self.audio.path

    if HAVE_SOX:
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
                valid_types = (', '.join(settings.VALID_AUDIO_FILE_TYPES.keys())).upper()

                audio_path = self.audio_path

                audio_ext = os.path.splitext(audio_path)[1].lower()
                valid_info = settings.VALID_AUDIO_FILE_TYPES.get(audio_ext)
                if not valid_info:
                    raise ValidationError({'audio': f"Invalid file extension: '{self.audio.name}'. "
                                                    f'Valid extensions: {valid_types}.'})

                mime = subprocess.check_output(['file', '--mime-type', '--brief', audio_path]).decode().strip()
                if not (
                    (mime.startswith('audio/') and mime.endswith(valid_info['mime']))
                    # Some cases where mp3s are octet-streams because of bizarro weird encoding
                    or (audio_ext == '.mp3' and mime == 'application/octet-stream')
                ):
                    expected_mime = f"audio/{valid_info['mime']}"
                    raise ValidationError({'audio': f"Detected mime type {mime} for '{self.audio.name}'. "
                                                    f'Expected {expected_mime} from extension {audio_ext}.'})

                try:
                    file_type = sox.file_info.file_type(audio_path).lower()
                except sox.SoxiError:
                    raise ValidationError({'audio': f"Error reading: '{self.audio.name}'. "
                                                    'Likely an invalid/corrupt audio file. Please re-encode file.'})
                else:
                    if file_type != valid_info['soxi']:
                        raise ValidationError({'audio': f"Detected file type {file_type} for '{self.audio.name}'. "
                                                        f'Expected {valid_info["soxi"]} from extension {audio_ext}.'})

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
