# standart modules
import math

# blender modules
import bpy

# addon modules
from . import base_utils
from . import uv_utils
from .. import version_utils


def set_lmap_uv(visuals_lmaps, lmap_uvs):
    preview_uv = {}
    for lmap_name, visuals_names in visuals_lmaps.items():
        for visual_name in visuals_names:
            visual_obj = bpy.data.objects[visual_name]
            preview_uv[visual_obj.name] = visual_obj.data.uv_layers.active.name
            uv_name = lmap_uvs[visual_obj.name]
            uv_layer = visual_obj.data.uv_layers[uv_name]
            visual_obj.data.uv_layers.active = uv_layer
    return preview_uv


def merge_objects():
    # find level object
    level_object = base_utils.get_level_object()
    # find visuals
    visuals, materials, lmap_uvs = base_utils.get_light_map_visuals(level_object)
    # sort visuals
    visuals_lmaps = base_utils.sort_visuals_by_light_maps(visuals, materials)
    # set light map uv and save preview uv
    preview_uv = set_lmap_uv(visuals_lmaps, lmap_uvs)
    # merge objects
    lmap_collection = version_utils.create_collection('Bake Light Map')
    mats = set()
    mat_table = {}
    for lmap_name, visuals_names in visuals_lmaps.items():
        if bpy.context.object:
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        lmap_visuals = []
        lmap_root_visual = bpy.data.objects.new(lmap_name, None)
        for visual_name in visuals_names:
            visual_obj = bpy.data.objects[visual_name]
            merged_mesh = visual_obj.data.copy()
            merged_obj = visual_obj.copy()
            merged_obj.data = merged_mesh
            merged_obj.parent = lmap_root_visual
            mat_name = materials[visual_obj.name]
            mat = bpy.data.materials[mat_name].copy()
            mats.add(mat)
            mat_table[visual_name] = mat
            merged_mesh.materials.clear()
            merged_mesh.materials.append(mat)
            version_utils.link_object_to_collection(merged_obj, lmap_collection)
            version_utils.select_object(merged_obj)
        version_utils.set_active_object(merged_obj)
        bpy.ops.object.join()
        merged_obj = lmap_root_visual.children[0]
        bpy.data.objects.remove(lmap_root_visual)
    # create images
    images = {}
    for lmap_name, visuals_names in visuals_lmaps.items():
        lmap_image = bpy.data.images.new('shadows_' + lmap_name, 1024, 1024)
        for visual_name in visuals_names:
            mat = mat_table[visual_name]
            images[mat.name] = lmap_image
    # add image node
    bake_images = {}
    for mat in mats:
        nodes = mat.node_tree.nodes
        bake_img = nodes.new('ShaderNodeTexImage')
        img = images[mat.name]
        bake_img.image = img
        min_loc_x = 1_000_000
        for node in mat.node_tree.nodes:
            node.select = False
            min_loc_x = min(min_loc_x, node.location.x)
        mat.node_tree.nodes.active = bake_img
        bake_img.select = True
        bake_img.location.x = min_loc_x - 1000
        bake_images[mat] = bake_img.name
        # remove texture color links
        links = mat.node_tree.links
        for link in links:
            node = link.to_node
            socket = link.to_socket
            if socket.name in ('Color', 'Base Color'):
                if node.bl_idname in (
                    'ShaderNodeBsdfDiffuse',
                    'ShaderNodeBsdfPrincipled',
                    'ShaderNodeEmission'
                ):
                    links.remove(link)
    # set preview uv
    uv_utils.set_preview_uv(preview_uv)
