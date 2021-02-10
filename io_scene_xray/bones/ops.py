# standart modules
import os

# blender modules
import bpy
from bpy_extras import io_utils

# addon modules
from .. import plugin, registry
from ..utils import execute_with_logger, set_cursor_state, AppError
from ..version_utils import assign_props, IS_28
from . import imp


op_import_bones_props = {
    'filter_glob': bpy.props.StringProperty(
        default='*.bones', options={'HIDDEN'}
    ),
    'directory': bpy.props.StringProperty(
        subtype="DIR_PATH", options={'SKIP_SAVE'}
    ),
    'files': bpy.props.CollectionProperty(
        type=bpy.types.OperatorFileListElement
    )
}


@registry.module_thing
class IMPORT_OT_xray_bones(bpy.types.Operator, io_utils.ImportHelper):
    bl_idname = 'xray_import.bones'
    bl_label = 'Import .bones'
    bl_description = 'Import X-Ray Bones Data'
    bl_options = {'UNDO'}

    if not IS_28:
        for prop_name, prop_value in op_import_bones_props.items():
            exec('{0} = op_import_bones_props.get("{0}")'.format(prop_name))

    @execute_with_logger
    @set_cursor_state
    def execute(self, _context):
        if len(self.files) > 1:
            self.report({'ERROR'}, 'Too many selected files. Select one file')
            return {'CANCELLED'}
        if not len(self.files):
            self.report({'ERROR'}, 'No file selected')
            return {'CANCELLED'}
        if not self.files[0].name:
            self.report({'ERROR'}, 'No file selected')
            return {'CANCELLED'}
        filename = self.files[0].name
        filepath = os.path.join(self.directory, filename)
        ext = os.path.splitext(filename)[-1].lower()
        if ext == '.bones':
            if not os.path.exists(filepath):
                self.report({'ERROR'}, 'File not found: "{}"'.format(filepath))
                return {'CANCELLED'}
            try:
                imp.import_file(filepath)
                return {'FINISHED'}
            except AppError as err:
                self.report({'ERROR'}, str(err))
                return {'CANCELLED'}
        else:
            self.report(
                {'ERROR'}, 'Format of "{}" not recognised'.format(filepath)
            )
            return {'CANCELLED'}

    def invoke(self, context, event):
        obj = bpy.context.object
        if not obj:
            self.report({'ERROR'}, 'There is no active object')
            return {'CANCELLED'}
        if obj.type != 'ARMATURE':
            self.report({'ERROR'}, 'The active object is not an armature')
            return {'CANCELLED'}
        return super().invoke(context, event)


assign_props([
    (op_import_bones_props, IMPORT_OT_xray_bones),
])


def menu_func_import(self, _context):
    icon = plugin.get_stalker_icon()
    self.layout.operator(
        IMPORT_OT_xray_bones.bl_idname,
        text='X-Ray Bones Data (.bones)', icon_value=icon
    )
