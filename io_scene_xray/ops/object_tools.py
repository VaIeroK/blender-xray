# standart modules
import zlib

# blender modules
import bpy
import mathutils

# addon modules
from .. import utils
from .. import version_utils


plane_items = (
    ('XY', 'XY', ''),
    ('XZ', 'XZ', '')
)
place_objects_props = {
    'plane': bpy.props.EnumProperty(
        name='Plane',
        default='XY',
        items=plane_items
    ),
    'rows': bpy.props.IntProperty(name='Rows', default=1, min=1, max=1000),
    'offset_x': bpy.props.FloatProperty(
        name='Horizontal Offset', default=2.0, min=0.001
    ),
    'offset_z': bpy.props.FloatProperty(
        name='Vertical Offset', default=2.0, min=0.001
    )
}


class XRAY_OT_place_objects(bpy.types.Operator):
    bl_idname = 'io_scene_xray.place_objects'
    bl_label = 'Place Selected Objects'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    if not version_utils.IS_28:
        for prop_name, prop_value in place_objects_props.items():
            exec('{0} = place_objects_props.get("{0}")'.format(prop_name))

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Plane:')
        row = column.row(align=True)
        row.prop(self, 'plane', expand=True)
        column.prop(self, 'rows')
        column.prop(self, 'offset_x')
        column.prop(self, 'offset_z')

    @utils.set_cursor_state
    def execute(self, context):
        objs = set()
        for obj in context.selected_objects:
            if obj.xray.isroot:
                objs.add(obj.name)
        objs = sorted(list(objs))
        objects_count = len(objs)
        column = 0
        row = 0
        objects_in_row = objects_count // self.rows
        if (objects_count % self.rows) == 0:
            offset = 1
        else:
            offset = 0
        for obj_name in objs:
            obj = bpy.data.objects.get(obj_name)
            obj.location.x = column * self.offset_x
            obj.location.y = 0.0
            if self.plane == 'XY':
                obj.location.y = row * self.offset_z
                obj.location.z = 0.0
            else:
                obj.location.y = 0.0
                obj.location.z = row * self.offset_z
            if ((column + offset) % objects_in_row) == 0 and column != 0:
                column = 0
                row += 1
            else:
                column += 1
        self.report({'INFO'}, 'Moved {0} objects'.format(objects_count))
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


colorize_mode_items = (
    ('ACTIVE_OBJECT', 'Active Object', ''),
    ('SELECTED_OBJECTS', 'Selected Objects', ''),
    ('ALL_OBJECTS', 'All Objects', '')
)
xray_colorize_objects_props = {
    'mode': bpy.props.EnumProperty(
        default='SELECTED_OBJECTS',
        items=colorize_mode_items
    ),
    'seed': bpy.props.IntProperty(min=0, max=255),
    'power': bpy.props.FloatProperty(default=0.5, min=0.0, max=1.0)
}


class XRAY_OT_colorize_objects(bpy.types.Operator):
    bl_idname = 'io_scene_xray.colorize_objects'
    bl_label = 'Colorize Objects'
    bl_description = 'Set a pseudo-random object color'
    bl_options = {'REGISTER', 'UNDO'}

    if not version_utils.IS_28:
        for prop_name, prop_value in xray_colorize_objects_props.items():
            exec('{0} = xray_colorize_objects_props.get("{0}")'.format(prop_name))

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        column.prop(self, 'seed', text='Seed')
        column.prop(self, 'power', text='Power', slider=True)
        column.label(text='Mode:')
        column.prop(self, 'mode', expand=True)

    @utils.set_cursor_state
    def execute(self, context):
        # active object
        if self.mode == 'ACTIVE_OBJECT':
            obj = context.active_object
            if not obj:
                self.report({'ERROR'}, 'No active object')
                return {'CANCELLED'}
            objects = (obj, )
        # selected objects
        elif self.mode == 'SELECTED_OBJECTS':
            objects = context.selected_objects
            if not objects:
                self.report({'ERROR'}, 'No objects selected')
                return {'CANCELLED'}
        # all objects
        elif self.mode == 'ALL_OBJECTS':
            objects = bpy.data.objects
            if not objects:
                self.report({'ERROR'}, 'Blend-file has no objects')
                return {'CANCELLED'}
        # colorize
        changed_objects_count = 0
        for obj in objects:
            data = bytearray(obj.name, 'utf8')
            data.append(self.seed)
            hsh = zlib.crc32(data)
            color = mathutils.Color()
            color.hsv = (
                (hsh & 0xFF) / 0xFF,
                (((hsh >> 8) & 3) / 3 * 0.5 + 0.5) * self.power,
                ((hsh >> 2) & 1) * (0.5 * self.power) + 0.5
            )
            color = [color.r, color.g, color.b]
            if version_utils.IS_28:
                color.append(1.0)    # alpha
            obj.color = color
            changed_objects_count += 1
        self.report(
            {'INFO'},
            'Changed {} material(s)'.format(changed_objects_count)
        )
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


classes = (
    (XRAY_OT_place_objects, place_objects_props),
    (XRAY_OT_colorize_objects, xray_colorize_objects_props)
)


def register():
    for operator, props in classes:
        if props:
            version_utils.assign_props([(props, operator), ])
        bpy.utils.register_class(operator)


def unregister():
    for operator, props in reversed(classes):
        bpy.utils.unregister_class(operator)
