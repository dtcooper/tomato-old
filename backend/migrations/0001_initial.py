# Generated by Django 3.0 on 2019-12-12 20:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=True, help_text='If this is checked, enabled to be randomly selected. If unchecked random selection is disabled, regardless of begin and end air date below.', verbose_name='Enabled')),
                ('begin', models.DateTimeField(blank=True, help_text='Optional date when eligibility for random selection *begins*. If specified, random selection is enabled after this date. (Timezone: US/Pacific)', null=True, verbose_name='Begin Air Date')),
                ('end', models.DateTimeField(blank=True, help_text='Optional date when eligibility for random selection *ends*. If specified, random selection is enabled before this date. (Timezone: US/Pacific)', null=True, verbose_name='End Air Date')),
                ('weight', models.PositiveSmallIntegerField(default=1, help_text="The weight (ie selection bias) for how likely random selection occurs, eg '1' is just as likely as all others,  '2' is 2x as likely, '3' is 3x as likely and so on.", verbose_name='Random Weight')),
                ('name', models.CharField(blank=True, db_index=True, max_length=50, verbose_name='Optional Name')),
                ('md5sum', models.CharField(max_length=32)),
                ('audio', models.FileField(upload_to='assets/', verbose_name='Audio File')),
            ],
            options={
                'verbose_name': 'Audio Asset',
                'verbose_name_plural': 'Audio Assets',
                'db_table': 'assets',
                'ordering': ('name', 'id'),
            },
        ),
        migrations.CreateModel(
            name='Rotator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, help_text="Category name of this asset rotator, eg 'ADs', 'Station IDs, 'Short Interviews', etc.", max_length=50, verbose_name='Rotator Name')),
                ('color', models.CharField(choices=[('ff8a80', 'Red'), ('ff80ab', 'Pink'), ('ea80fc', 'Purple'), ('b388ff', 'Deep Purple'), ('8c9eff', 'Indigo'), ('82b1ff', 'Blue'), ('80d8ff', 'Light Blue'), ('84ffff', 'Cyan'), ('a7ffeb', 'Teal'), ('b9f6ca', 'Green'), ('ccff90', 'Light Green'), ('f4ff81', 'Lime'), ('ffff8d', 'Yellow'), ('ffe57f', 'Amber'), ('ffd180', 'Orange'), ('ff9e80', 'Deep Orange')], default='ff8a80', help_text='Color that appears in the playout software for assets in this rotator.', max_length=6, verbose_name='Color')),
            ],
            options={
                'verbose_name': 'Rotator',
                'verbose_name_plural': 'Rotators',
                'db_table': 'rotators',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='StopSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=True, help_text='If this is checked, enabled to be randomly selected. If unchecked random selection is disabled, regardless of begin and end air date below.', verbose_name='Enabled')),
                ('begin', models.DateTimeField(blank=True, help_text='Optional date when eligibility for random selection *begins*. If specified, random selection is enabled after this date. (Timezone: US/Pacific)', null=True, verbose_name='Begin Air Date')),
                ('end', models.DateTimeField(blank=True, help_text='Optional date when eligibility for random selection *ends*. If specified, random selection is enabled before this date. (Timezone: US/Pacific)', null=True, verbose_name='End Air Date')),
                ('weight', models.PositiveSmallIntegerField(default=1, help_text="The weight (ie selection bias) for how likely random selection occurs, eg '1' is just as likely as all others,  '2' is 2x as likely, '3' is 3x as likely and so on.", verbose_name='Random Weight')),
                ('name', models.CharField(max_length=50, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'Stop Set',
                'verbose_name_plural': 'Stop Sets',
                'db_table': 'stopsets',
            },
        ),
        migrations.CreateModel(
            name='StopSetRotator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rotator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.Rotator', verbose_name='Rotator')),
                ('stopset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.StopSet')),
            ],
            options={
                'verbose_name': 'Stop Set Rotator Entry',
                'verbose_name_plural': 'Stop Set Rotator Entries',
                'db_table': 'stopset_rotators',
                'ordering': ('id',),
            },
        ),
        migrations.CreateModel(
            name='RotatorAsset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.Asset')),
                ('rotator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.Rotator', verbose_name='Rotator')),
            ],
            options={
                'verbose_name': 'Rotator',
                'verbose_name_plural': 'Rotators',
                'db_table': 'rotator_assets',
                'ordering': ('id',),
            },
        ),
        migrations.AddField(
            model_name='rotator',
            name='stopsets',
            field=models.ManyToManyField(related_name='rotators', through='backend.StopSetRotator', to='backend.StopSet'),
        ),
        migrations.AddField(
            model_name='asset',
            name='rotators',
            field=models.ManyToManyField(related_name='assets', through='backend.RotatorAsset', to='backend.Rotator'),
        ),
        migrations.CreateModel(
            name='ApiToken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(db_index=True, max_length=36)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'api_tokens',
                'unique_together': {('token', 'user')},
            },
        ),
    ]
