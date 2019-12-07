from .models import AssetRotation


def ad_rotation_colors(request):
    return {'ad_rotation_colors': dict(AssetRotation.objects.values_list('id', 'color'))}
