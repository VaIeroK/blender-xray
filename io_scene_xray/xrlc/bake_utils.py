# standart modules
import math

# blender modules
import bpy

# addon modules
from . import base_utils
from . import uv_utils
from .. import version_utils


def set_render_settings(operator):
    scn = bpy.context.scene
    rend = scn.render
    if rend.engine != 'CYCLES':
        rend.engine = 'CYCLES'
    cycles = scn.cycles
    cycles.samples = operator.samples
    cycles.adaptive_min_samples = operator.samples
    # set bake settings
    rend.use_bake_multires = False
    rend.bake.use_selected_to_active = False
    rend.bake.target = 'IMAGE_TEXTURES'
    rend.bake.use_clear = True
    rend.bake.margin = 4


def set_lmap_uv(visuals, lmap_uvs):
    preview_uv = {}
    for lmap_name, visuals_names in visuals.items():
        for visual_name in visuals_names:
            visual_obj = bpy.data.objects[visual_name]
            preview_uv[visual_obj.name] = visual_obj.data.uv_layers.active.name
            uv_name = lmap_uvs[visual_obj.name]
            uv_layer = visual_obj.data.uv_layers[uv_name]
            visual_obj.data.uv_layers.active = uv_layer
    return preview_uv


def bake(visuals, materials):
    visuals_obj = []
    images = {}
    # create images
    for lmap_name, visuals_names in visuals.items():
        lmap_image = bpy.data.images.new('shadows_' + lmap_name, 1024, 1024)
        for visual_name in visuals_names:
            mat_name = materials[visual_name]
            images[mat_name] = lmap_image
    # collect materials
    mats = set()
    for mat_name in materials.values():
        material = bpy.data.materials[mat_name]
        mats.add(material)
    # add image node
    bake_images = {}
    for mat in mats:
        nodes = mat.node_tree.nodes
        bake_img = nodes.new('ShaderNodeTexImage')
        img = images[mat.name]
        bake_img.image = img
        for node in mat.node_tree.nodes:
            node.select = False
        mat.node_tree.nodes.active = bake_img
        bake_img.select = True
        bake_img.location.x = -2000
        bake_images[mat] = bake_img.name
    # hide lights
    light_objects = []
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            light_objects.append(obj.name)
            obj.hide_render = True
    # create sun
    sun = bpy.data.lights.new('xrlc_sun', 'SUN')
    sun_obj = bpy.data.objects.new('xrlc_sun', sun)
    sun_obj.rotation_mode = 'XYZ'
    sun_obj.rotation_euler.y = math.radians(45)
    sun_obj.rotation_euler.z = math.radians(45)
    sun_obj.scale = (10, 10, 10)
    version_utils.link_object(sun_obj)
    # bake
    for lmap_name, visuals_names in visuals.items():
        if bpy.context.object:
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        for visual_name in visuals_names:
            visual_obj = bpy.data.objects[visual_name]
            print(visual_obj.name)
            version_utils.select_object(visual_obj)
            visuals_obj.append(visual_obj)
        version_utils.set_active_object(visuals_obj[0])
        return
        print('bake', lmap_name)
        bpy.ops.object.bake(type='SHADOW', use_clear=False)
    # remove temp data
    for mat, img_node_name in bake_images.items():
        nodes = mat.node_tree.nodes
        img_node = nodes[img_node_name]
        nodes.remove(img_node)
    bpy.data.objects.remove(sun_obj)
    bpy.data.lights.remove(sun)
    for light_name in light_objects:
        light = bpy.data.objects[light_name]
        light.hide_viewport = False


def bake_shadows_mode(operator, visuals, materials, lmap_uvs, bake_type):
    set_render_settings(operator)
    scn = bpy.context.scene
    scn.cycles.bake_type = bake_type
    preview_uv = set_lmap_uv(visuals, lmap_uvs)
    bake(visuals, materials)
    #uv_utils.set_preview_uv(preview_uv)


def bake_shadows(operator):
    level_object = base_utils.get_level_object()
    visuals, materials, lmap_uvs = base_utils.get_light_map_visuals(level_object)
    visuals_lmaps = base_utils.sort_visuals_by_light_maps(visuals, materials)
    bake_shadows_mode(operator, visuals_lmaps, materials, lmap_uvs, 'SHADOW')
