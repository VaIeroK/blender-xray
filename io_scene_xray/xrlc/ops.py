# blender modules
import bpy

# addon modules
from . import uv_utils
from . import bake_utils
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


bake_shadows_props = {
    'samples': bpy.props.IntProperty(name='Samples', default=10),
}


class XRAY_OT_bake_shadows(bpy.types.Operator):
    bl_idname = 'io_scene_xray.bake_shadows'
    bl_label = 'Bake Shadows'
    bl_options = {'REGISTER', 'UNDO'}

    if not version_utils.IS_28:
        for prop_name, prop_value in bake_shadows_props.items():
            exec('{0} = bake_shadows_props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)

        column.prop(self, 'samples')

    def execute(self, context):
        try:
            bake_utils.bake_shadows(self)
        except utils.AppError as err:
            self.report({'ERROR'}, str(err))
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


classes = (
    (XRAY_OT_build_lmap_uv, None),
    (XRAY_OT_bake_shadows, bake_shadows_props)
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
