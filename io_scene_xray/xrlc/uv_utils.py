# blender modules
import bpy

# addon modules
from . import base_utils
from .. import version_utils


def set_preview_uv(preview_uv):
    for visual_name, uv_name in preview_uv.items():
        visual_obj = bpy.data.objects[visual_name]
        uv_layer = visual_obj.data.uv_layers[uv_name]
        visual_obj.data.uv_layers.active = uv_layer


def generate_uv(visuals, lmap_uvs):
    preview_uv = {}
    for lmap_name, visuals_names in visuals.items():
        print(lmap_name)
        if bpy.context.object:
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        visual_objs = []
        for visual_name in visuals_names:
            visual_obj = bpy.data.objects[visual_name]
            version_utils.select_object(visual_obj)
            visual_objs.append(visual_obj)
            preview_uv[visual_obj.name] = visual_obj.data.uv_layers.active.name
            uv_name = lmap_uvs[visual_obj.name]
            uv_layer = visual_obj.data.uv_layers[uv_name]
            visual_obj.data.uv_layers.active = uv_layer
        version_utils.set_active_object(visual_objs[0])
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')
        print('\tuv cube project')
        bpy.ops.uv.cube_project()
        bpy.ops.uv.reveal()
        bpy.ops.uv.select_all(action='SELECT')
        print('\tuv pack islands')
        bpy.ops.uv.pack_islands(margin=0.001)
        bpy.ops.object.mode_set(mode='OBJECT')
    set_preview_uv(preview_uv)


def build_lmap_uv():
    level_object = base_utils.get_level_object()
    visuals, materials, lmap_uvs = base_utils.get_light_map_visuals(level_object)
    visuals_lmaps = base_utils.sort_visuals_by_light_maps(visuals, materials)
    generate_uv(visuals_lmaps, lmap_uvs)
