# blender modules
import bpy

# addon modules
from .. import utils


def get_level_object():
    # collect game level root-objects
    level_objects = []
    for bpy_object in bpy.data.objects:
        if bpy_object.xray.level.object_type == 'LEVEL':
            level_objects.append(bpy_object)

    # if there is only one level in the scene
    level_objects_count = len(level_objects)
    if level_objects_count == 1:
        return level_objects[0]

    # check active object and try to use it
    bpy_object = bpy.context.object
    if bpy_object:
        if bpy_object.xray.level.object_type == 'LEVEL':
            return bpy_object

    # if the scene has several levels,
    # then it is not clear which one should be used
    if level_objects_count > 1:
        raise utils.AppError('there is more than one level-object')

    if not level_objects:
        raise utils.AppError('missing level-object')


def get_children():
    children = {}

    for obj in bpy.data.objects:
        children[obj.name] = []

    for child_obj in bpy.data.objects:
        parent = child_obj.parent
        if parent:
            children[parent.name].append(child_obj.name)

    return children


def is_lmap_visual(visual_obj, materials, lmap_uvs):
    slots_count = len(visual_obj.material_slots)
    mesh = visual_obj.data
    material = None

    # no materials
    if not slots_count:
        return

    # single-material
    elif slots_count == 1:
        slot = visual_obj.material_slots[0]
        mat = slot.material
        if mat:
            material = mat

    # multiple-material
    else:
        used_slots = set()
        for face in mesh.polygons:
            mat_index = face.material_index
            used_slots.add(mat_index)
        used_materials = set()
        for slot_index in used_slots:
            slot = visual_obj.material_slots[slot_index]
            mat = slot.material
            if mat:
                used_materials.add(mat)
        if len(used_materials) == 1:
            material = list(used_materials)[0]

    # validate material
    if material:
        xray = material.xray
        if xray.lmap_0 and xray.lmap_1:
            lmap_uv = mesh.uv_layers.get(xray.uv_light_map)
            if lmap_uv:
                materials[visual_obj.name] = material.name
                lmap_uvs[visual_obj.name] = lmap_uv.name
                return True


def get_visual_recursive(children_table, visuals, materials, lmap_uvs, parent_name):
    children_names = children_table[parent_name]
    for children_name in children_names:
        child_object = bpy.data.objects[children_name]
        lvl_props = child_object.xray.level
        if child_object.xray.is_level:
            if lvl_props.object_type == 'VISUAL':
                if lvl_props.visual_type in {'NORMAL', 'PROGRESSIVE'}:
                    if is_lmap_visual(child_object, materials, lmap_uvs):
                        visuals.add(child_object.name)
        get_visual_recursive(
            children_table,
            visuals,
            materials,
            lmap_uvs,
            child_object.name
        )


def get_light_map_visuals(level_object):
    children = get_children()
    visuals = set()
    materials = {}
    lmap_uvs = {}
    get_visual_recursive(children, visuals, materials, lmap_uvs, level_object.name)
    visuals = list(visuals)
    visuals.sort()
    return visuals, materials, lmap_uvs


def sort_visuals_by_light_maps(visual_names, materials_table):
    sorted_visuals = {}
    for visual_name in visual_names:
        material_name = materials_table[visual_name]
        bpy_obj = bpy.data.objects[visual_name]
        mat = bpy.data.materials[material_name]
        lmap_name = mat.xray.lmap_0
        sorted_visuals.setdefault(lmap_name, []).append(visual_name)
    return sorted_visuals
