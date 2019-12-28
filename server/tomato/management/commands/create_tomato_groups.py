from django.core.management.base import BaseCommand

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from tomato.models import Asset, Rotator, StopSet, StopSetRotator


class Command(BaseCommand):
    def handle(self, *args, **options):
        asset = ContentType.objects.get_for_model(Asset)
        all_models = (
            asset,
            ContentType.objects.get_for_model(Rotator),
            ContentType.objects.get_for_model(StopSet),
            ContentType.objects.get_for_model(StopSetRotator),
        )

        group, _ = Group.objects.get_or_create(name='Edit Rotators, Stop Sets & Audio Assets')
        group.permissions.add(*Permission.objects.filter(content_type__in=all_models))

        group, _ = Group.objects.get_or_create(name='Edit Audio Assets only, view Rotators & Stop Sets')
        group.permissions.add(*Permission.objects.filter(content_type__in=all_models,
                                                         codename__startswith='view_'))
        group.permissions.add(*Permission.objects.filter(content_type=asset))

        group, _ = Group.objects.get_or_create(name='View Rotators, Stop Sets & Audio Assets')
        group.permissions.add(*Permission.objects.filter(content_type__in=all_models,
                                                         codename__startswith='view_'))

        group, _ = Group.objects.get_or_create(name='Modify site-wide configuration')
        group.permissions.add(Permission.objects.get(codename='change_config'))
