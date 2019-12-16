from .models import Rotator


def rotator_colors(request):
    return {'rotator_colors': dict(Rotator.objects.values_list('id', 'color'))}
