import bpy

from .. import registry, plugin_prefs
from ..version_utils import assign_props


import_skls_props = {
    'motion_index': bpy.props.IntProperty(),
}


class ImportSkls(bpy.types.PropertyGroup):
    pass


xray_scene_properties = {
    'export_root': bpy.props.StringProperty(
        name='Export Root',
        description='The root folder for export',
        subtype='DIR_PATH',
    ),
    'fmt_version': plugin_prefs.PropSDKVersion(),
    'object_export_motions': plugin_prefs.PropObjectMotionsExport(),
    'object_texture_name_from_image_path': plugin_prefs.PropObjectTextureNamesFromPath(),
    'materials_colorize_random_seed': bpy.props.IntProperty(min=0, max=255, options={'SKIP_SAVE'}),
    'materials_colorize_color_power': bpy.props.FloatProperty(
        default=0.5, min=0.0, max=1.0,
        options={'SKIP_SAVE'},
    ),
    'import_skls': bpy.props.PointerProperty(type=ImportSkls)
}


@registry.requires(ImportSkls)
class XRaySceneProperties(bpy.types.PropertyGroup):
    b_type = bpy.types.Scene


assign_props([
    (import_skls_props, ImportSkls),
    (xray_scene_properties, XRaySceneProperties)
])
