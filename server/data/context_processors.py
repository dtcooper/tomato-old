from .models import Rotator


def extra_admin_context(request):
    return {'rotator_colors': dict(Rotator.objects.values_list('id', 'color'))}
