# Generated by Django 3.0.3 on 2020-03-03 23:08

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LogEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('created', models.DateTimeField()),
                ('user_id', models.IntegerField(db_index=True)),
                ('action', models.PositiveSmallIntegerField(choices=[(1, 'Played Asset'), (2, 'Skipped Asset'), (3, 'Played entire Stop Set'), (4, 'Played a partial Stop Set'), (5, 'Skipped entire Stop Set'), (6, 'Waited')], db_index=True)),
                ('duration', models.DurationField(null=True)),
                ('description', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'Client Log Entry',
                'verbose_name_plural': 'Client Log Entries',
                'db_table': 'log_entries',
            },
        ),
        migrations.CreateModel(
            name='Rotator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, help_text="Category name of this asset rotator, eg 'ADs', 'Station IDs, 'Short Interviews', etc.", max_length=75, verbose_name='Rotator Name')),
                ('color', models.CharField(choices=[('red', 'Red'), ('pink', 'Pink'), ('purple', 'Purple'), ('deep-purple', 'Deep Purple'), ('indigo', 'Indigo'), ('blue', 'Blue'), ('light-blue', 'Light Blue'), ('cyan', 'Cyan'), ('teal', 'Teal'), ('green', 'Green'), ('light-green', 'Light Green'), ('lime', 'Lime'), ('yellow', 'Yellow'), ('amber', 'Amber'), ('orange', 'Orange'), ('deep-orange', 'Deep Orange')], default='red', help_text='Color that appears in the playout software for assets in this rotator.', max_length=20, verbose_name='Color')),
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
                ('begin', models.DateTimeField(blank=True, help_text='Optional date when eligibility for random selection *begins*. If specified, random selection is eligible after this date.', null=True, verbose_name='Begin Air Date')),
                ('end', models.DateTimeField(blank=True, help_text='Optional date when eligibility for random selection *ends*. If specified, random selection is eligible before this date.', null=True, verbose_name='End Air Date')),
                ('weight', models.DecimalField(decimal_places=2, default=1, help_text="The weight (ie selection bias) for how likely random selection occurs, eg '1' is just as likely as all others, '2' is 2x as likely, '3' is 3x as likely, '0.5' half as likely, and so on.", max_digits=5, verbose_name='Random Weight')),
                ('name', models.CharField(max_length=75, verbose_name='Name')),
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
                ('rotator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tomato.Rotator', verbose_name='Rotator')),
                ('stopset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tomato.StopSet')),
            ],
            options={
                'verbose_name': 'Rotator in Stop Set relationship',
                'verbose_name_plural': 'Rotator in Stop Set relationships',
                'db_table': 'stopset_rotators',
                'ordering': ('id',),
            },
        ),
        migrations.AddField(
            model_name='rotator',
            name='stopsets',
            field=models.ManyToManyField(related_name='rotators', through='tomato.StopSetRotator', to='tomato.StopSet', verbose_name='Stop Set'),
        ),
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enabled', models.BooleanField(default=True, help_text='If this is checked, enabled to be randomly selected. If unchecked random selection is disabled, regardless of begin and end air date below.', verbose_name='Enabled')),
                ('begin', models.DateTimeField(blank=True, help_text='Optional date when eligibility for random selection *begins*. If specified, random selection is eligible after this date.', null=True, verbose_name='Begin Air Date')),
                ('end', models.DateTimeField(blank=True, help_text='Optional date when eligibility for random selection *ends*. If specified, random selection is eligible before this date.', null=True, verbose_name='End Air Date')),
                ('weight', models.DecimalField(decimal_places=2, default=1, help_text="The weight (ie selection bias) for how likely random selection occurs, eg '1' is just as likely as all others, '2' is 2x as likely, '3' is 3x as likely, '0.5' half as likely, and so on.", max_digits=5, verbose_name='Random Weight')),
                ('name', models.CharField(blank=True, db_index=True, help_text="Optional name, if left unspecified, we'll base it off the audio file's metadata, failing that its filename.", max_length=75, verbose_name='Name')),
                ('duration', models.DurationField()),
                ('audio', models.FileField(upload_to='assets/', verbose_name='Audio File')),
                ('audio_size', models.BigIntegerField()),
                ('rotators', models.ManyToManyField(blank=True, help_text='Rotators that this asset will be included in.', related_name='assets', to='tomato.Rotator', verbose_name='Rotators')),
            ],
            options={
                'verbose_name': 'Audio Asset',
                'verbose_name_plural': 'Audio Assets',
                'db_table': 'assets',
                'ordering': ('name', 'id'),
            },
        ),
    ]
