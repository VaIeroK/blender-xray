# blender modules
import bpy

# addon modules
from . import uv_utils
from . import geom_utils
from .. import version_utils
from .. import utils


class XRAY_OT_build_lmap_uv(bpy.types.Operator):
    bl_idname = 'io_scene_xray.build_lmap_uv'
    bl_label = 'Build UV'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            uv_utils.build_lmap_uv()
        except utils.AppError as err:
            self.report({'ERROR'}, str(err))
        return {'FINISHED'}


class XRAY_OT_merge_objects(bpy.types.Operator):
    bl_idname = 'io_scene_xray.merge_objects'
    bl_label = 'Merge Objects'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        try:
            geom_utils.merge_objects()
        except utils.AppError as err:
            self.report({'ERROR'}, str(err))
        return {'FINISHED'}


classes = (
    (XRAY_OT_build_lmap_uv, None),
    (XRAY_OT_merge_objects, None)
)


def register():
    for clas, props in classes:
        if props:
            version_utils.assign_props(
                [(props, clas), ]
            )
        bpy.utils.register_class(clas)


def unregister():
    for clas, props in reversed(classes):
        bpy.utils.unregister_class(clas)
