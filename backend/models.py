from django.conf import settings
from django.contrib.humanize.templatetags.humanize import ordinal
from django.db import models


class EnabledBeginEndWeightMixin(models.Model):
    enabled = models.BooleanField(
        default=True,
        help_text=('If this is checked, enabled to be randomly selected. If unchecked '
                   'selection is disabled, regardless of begin and end date below.'))
    begin = models.DateTimeField(
        'Begin Date', null=True, blank=True,
        help_text=('Optional date when eligibility for random selection *begins*. If specified, '
                   f'selection is disabled after this date. (Timezone: {settings.TIME_ZONE})'))
    end = models.DateTimeField(
        'End Date', null=True, blank=True,
        help_text=('Optional date when eligibility for random selection *ends*. If specified, '
                   f'selection is disabled after this date. (Timezone: {settings.TIME_ZONE})'))
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
        return f'{"" if self.enabled else "[DISABLED] "}{self.name}'

    class Meta:
        verbose_name = 'Stop Set'
        verbose_name_plural = 'Stop Sets'


class AssetRotation(models.Model):
    name = models.CharField(
        'Rotation Name', max_length=50,
        help_text=("Category name of this asset rotation, eg 'AD', 'Station ID', "
                   "'Diary of the Dust', etc."))
    color = models.CharField(
        default='80d8ff', max_length=6,
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
    stop_sets = models.ManyToManyField(
        StopSet,
        through='StopSetEntry',
        through_fields=('asset_rotation', 'stop_set'))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Asset Rotation'
        verbose_name_plural = 'Asset Rotations'
        ordering = ('name',)


class StopSetEntryQuerySet(models.QuerySet):
    def ordered(self):
        return self.annotate(
            ordering_sign=models.Case(
                models.When(ordering__lt=0, then=models.Value(1)),
                default=models.Value(0),
                output_field=models.IntegerField(),
            )
        ).order_by('ordering_sign', 'ordering')


class StopSetEntry(models.Model):
    # objects = StopSetEntryQuerySet.as_manager()

    # TODO: Maybe get rid of ordering and use natural ordering
    # TODO: get rid of this intermediary model (potentially unneeded)
    # ordering = models.SmallIntegerField(
    #     'Sort Order Hint', default=1,
    #     help_text=('Where this rotation should play. Negative numbers play from the end, eg '
    #                "'-1' is last and '-2' is 2nd last. Equal values order randomly. "))
    stop_set = models.ForeignKey(StopSet, on_delete=models.CASCADE)
    asset_rotation = models.ForeignKey(
        AssetRotation, on_delete=models.CASCADE, verbose_name='Asset Rotation')

    def __str__(self):
        return self.asset_rotation.name

    class Meta:
        verbose_name = 'Rotation Entry'
        verbose_name_plural = 'Rotation Entries'
        ordering = ('id',)


class Asset(EnabledBeginEndWeightMixin, models.Model):
    label = models.CharField(max_length=50)
    # md5_sum
    # file
