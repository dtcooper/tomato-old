from .models import Rotation


def rotation_colors(request):
    return {'rotation_colors': dict(Rotation.objects.values_list('id', 'color'))}
