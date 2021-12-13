# blender modules
import bpy

# addon modules
from .. import ui
from .. import utils
from .. import details
from .. import version_utils
from .. import xray_ltx


items = (
    ('copy', '', '', 'COPYDOWN', 0),
    ('paste', '', '', 'PASTEDOWN', 1),
    ('clear', '', '', 'X', 2)
)
prop_clip_op_props = {
    'oper': bpy.props.EnumProperty(items=items),
    'path': bpy.props.StringProperty()
}
TRANSLATION_TEXT = 'Translation'
ROTATION_TEXT = 'Rotation'


class XRAY_OT_prop_clip(bpy.types.Operator):
    bl_idname = 'io_scene_xray.propclip'
    bl_label = ''

    if not version_utils.IS_28:
        for prop_name, prop_value in prop_clip_op_props.items():
            exec('{0} = prop_clip_op_props.get("{0}")'.format(prop_name))

    def execute(self, context):
        *path, prop = self.path.split('.')
        obj = context
        for name in path:
            obj = getattr(obj, name)
        if self.oper == 'copy':
            context.window_manager.clipboard = getattr(obj, prop)
        elif self.oper == 'paste':
            setattr(obj, prop, context.window_manager.clipboard)
        elif self.oper == 'clear':
            setattr(obj, prop, '')
        return {'FINISHED'}

    @classmethod
    def drawall(cls, layout, path, value):
        for item in items:
            row = layout.row(align=True)
            if item[0] in ('copy', 'clear') and not value:
                row.enabled = False
            props = row.operator(cls.bl_idname, icon=item[3])
            props.oper = item[0]
            props.path = path


class XRAY_UL_motion_list(bpy.types.UIList):
    bl_idname = 'XRAY_UL_motion_list'

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        data = context.object.xray
        motion = data.motions_collection[index]

        if data.motions_collection_index == index:
            icon = 'CHECKBOX_HLT'
        else:
            icon = 'CHECKBOX_DEHLT'

        row = layout.row()
        row.label(text='', icon=icon)
        row.prop_search(motion, 'name', bpy.data, 'actions', text='')
        if data.use_custom_motion_names:
            row.prop(motion, 'export_name', icon_only=True)


class XRAY_OT_add_all_actions(bpy.types.Operator):
    bl_idname = 'io_scene_xray.add_all_actions'
    bl_label = 'Add All Actions'
    bl_description = 'Add all actions to motion list'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not obj:
            return False
        return True

    def execute(self, context):
        obj = context.object
        for action in bpy.data.actions:
            if not obj.xray.motions_collection.get(action.name):
                motion = obj.xray.motions_collection.add()
                motion.name = action.name
        return {'FINISHED'}


class XRAY_OT_remove_all_actions(bpy.types.Operator):
    bl_idname = 'io_scene_xray.remove_all_actions'
    bl_label = 'Remove All Actions'
    bl_description = 'Remove all actions'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not obj:
            return False
        data = obj.xray
        motions_count = len(data.motions_collection)
        return bool(motions_count)

    def execute(self, context):
        obj = context.object
        obj.xray.motions_collection.clear()
        return {'FINISHED'}


class XRAY_OT_clean_actions(bpy.types.Operator):
    bl_idname = 'io_scene_xray.clean_actions'
    bl_label = 'Clean Actions'
    bl_description = 'Remove non-existent actions'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not obj:
            return False
        return True

    def execute(self, context):
        obj = context.object
        remove = []
        available = set()
        for motion_index, motion in enumerate(obj.xray.motions_collection):
            action = bpy.data.actions.get(motion.name)
            if not action:
                remove.append(motion_index)
            if motion.name in available:
                remove.append(motion_index)
            available.add(motion.name)
        remove.sort()
        remove.reverse()
        for motion_index in remove:
            obj.xray.motions_collection.remove(motion_index)
        return {'FINISHED'}


MOTION_NAME_PARAM = 'motion_name'
EXPORT_NAME_PARAM = 'export_name'


class XRAY_OT_copy_actions_list(bpy.types.Operator):
    bl_idname = 'io_scene_xray.copy_actions_list'
    bl_label = 'Copy Actions'
    bl_description = 'Copy actions list to clipboard'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not obj:
            return False
        return True

    def execute(self, context):
        obj = context.object
        lines = []
        saved_motions = set()
        for motion_index, motion in enumerate(obj.xray.motions_collection):
            if not motion.name:
                continue
            motion_key = (motion.name, motion.export_name)
            if motion_key in saved_motions:
                continue
            lines.append('[{}]\n{} = "{}"\n{} = "{}"\n'.format(
                motion_index,
                MOTION_NAME_PARAM,
                motion.name,
                EXPORT_NAME_PARAM,
                motion.export_name
            ))
            saved_motions.add(motion_key)
        bpy.context.window_manager.clipboard = '\n'.join(lines)
        return {'FINISHED'}


class XRAY_OT_paste_actions_list(bpy.types.Operator):
    bl_idname = 'io_scene_xray.paste_actions_list'
    bl_label = 'Past Actions'
    bl_description = 'Paste actions list from clipboard'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not obj:
            return False
        return True

    def execute(self, context):
        obj = context.object
        motions = obj.xray.motions_collection
        motions_data = bpy.context.window_manager.clipboard
        ltx = xray_ltx.StalkerLtxParser(None, data=motions_data)
        section_keys = list(map(int, ltx.sections.keys()))
        section_keys.sort()
        use_custom_name = False
        used_motions = {
            (motion.name, motion.export_name)
            for motion in obj.xray.motions_collection
        }
        for section_key in section_keys:
            section = ltx.sections[str(section_key)]
            params = section.params
            motion_name = params.get(MOTION_NAME_PARAM, None)
            export_name = params.get(EXPORT_NAME_PARAM, None)
            if not motion_name:
                continue
            motion_key = (motion_name, export_name)
            if motion_key in used_motions:
                continue
            motion = motions.add()
            motion.name = motion_name
            if export_name:
                motion.export_name = export_name
                use_custom_name = True
        if use_custom_name:
            obj.xray.use_custom_motion_names = True
        return {'FINISHED'}


def draw_motion_list_elements(layout):
    layout.operator(XRAY_OT_add_all_actions.bl_idname, text='', icon='ACTION')
    layout.operator(XRAY_OT_clean_actions.bl_idname, text='', icon='BRUSH_DATA')
    layout.operator(XRAY_OT_remove_all_actions.bl_idname, text='', icon='X')
    layout.operator(XRAY_OT_copy_actions_list.bl_idname, text='', icon='COPYDOWN')
    layout.operator(XRAY_OT_paste_actions_list.bl_idname, text='', icon='PASTEDOWN')


class XRAY_OT_remove_all_motion_refs(bpy.types.Operator):
    bl_idname = 'io_scene_xray.remove_all_motion_refs'
    bl_label = 'Remove All'
    bl_description = 'Remove all motion references'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not obj:
            return False
        data = obj.xray
        refs_count = len(data.motionrefs_collection)
        return bool(refs_count)

    def execute(self, context):
        obj = context.object
        obj.xray.motionrefs_collection.clear()
        return {'FINISHED'}


MOTION_NAME_PARAM = 'motion_name'
EXPORT_NAME_PARAM = 'export_name'


class XRAY_OT_copy_motion_refs_list(bpy.types.Operator):
    bl_idname = 'io_scene_xray.copy_motion_refs_list'
    bl_label = 'Copy Motion References'
    bl_description = 'Copy motion references list to clipboard'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not obj:
            return False
        return True

    def execute(self, context):
        obj = context.object
        lines = []
        saved_refs = set()
        for ref_index, ref in enumerate(obj.xray.motionrefs_collection):
            name = ref.name
            if not name:
                continue
            if name in saved_refs:
                continue
            unique_chars = set(name)
            if unique_chars == {' ', }:
                continue
            lines.append(name)
            saved_refs.add(name)
        bpy.context.window_manager.clipboard = '\n'.join(lines)
        return {'FINISHED'}


class XRAY_OT_paste_motion_refs_list(bpy.types.Operator):
    bl_idname = 'io_scene_xray.paste_motion_refs_list'
    bl_label = 'Past Motion References'
    bl_description = 'Paste motion references list from clipboard'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not obj:
            return False
        return True

    def execute(self, context):
        obj = context.object
        refs = obj.xray.motionrefs_collection
        used_refs = {ref.name for ref in obj.xray.motionrefs_collection}
        refs_data = bpy.context.window_manager.clipboard
        for line in refs_data.split('\n'):
            if not line:
                continue
            if line in used_refs:
                continue
            unique_chars = set(line)
            if unique_chars == {' ', }:
                continue
            ref = refs.add()
            ref.name = line
        return {'FINISHED'}


def draw_motion_refs_elements(layout):
    layout.operator(XRAY_OT_remove_all_motion_refs.bl_idname, text='', icon='X')
    layout.operator(XRAY_OT_copy_motion_refs_list.bl_idname, text='', icon='COPYDOWN')
    layout.operator(XRAY_OT_paste_motion_refs_list.bl_idname, text='', icon='PASTEDOWN')


def details_draw_function(self, context):
    box = self.layout.box()

    if not (context.object.type in {'MESH', 'EMPTY'}):
        box.label(
            text='Active object is not a mesh or empty',
            icon='ERROR'
        )
        return

    if context.active_object.type == 'MESH':

        model = context.object.xray.detail.model

        col = box.column(align=True)
        col.label(text='Detail Model Properties:')

        col.prop(model, 'no_waving', text='No Waving', toggle=True)
        col.prop(model, 'min_scale', text='Min Scale')
        col.prop(model, 'max_scale', text='Max Scale')
        col.prop(model, 'index', text='Detail Index')
        col.prop(model, 'color', text='')

    elif context.active_object.type == 'EMPTY':

        slots = context.object.xray.detail.slots

        box.label(text='Level Details Properties:')

        split = version_utils.layout_split(box, 0.4, align=True)
        split.label(text='Meshes Object:')
        split.prop_search(
            slots,
            'meshes_object',
            bpy.data,
            'objects',
            text=''
            )

        split = version_utils.layout_split(box, 0.4, align=True)
        split.label(text='Slots Base Object:')
        split.prop_search(
            slots,
            'slots_base_object',
            bpy.data,
            'objects',
            text=''
            )

        split = version_utils.layout_split(box, 0.4, align=True)
        split.label(text='Slots Top Object:')
        split.prop_search(
            slots,
            'slots_top_object',
            bpy.data,
            'objects',
            text=''
            )

        _, box_ = ui.collapsible.draw(
            box, 'object:lighting', 'Lighting Coefficients'
            )

        if box_:

            ligthing = slots.ligthing
            box_.label(text='Format:')
            row = box_.row()
            row.prop(ligthing, 'format', expand=True, text='Format')

            box_.prop_search(
                ligthing,
                'lights_image',
                bpy.data,
                'images',
                text='Lights'
                )

            if ligthing.format == 'builds_1569-cop':

                box_.prop_search(
                    ligthing,
                    'hemi_image',
                    bpy.data,
                    'images',
                    text='Hemi'
                    )

                box_.prop_search(
                    ligthing,
                    'shadows_image',
                    bpy.data,
                    'images',
                    text='Shadows'
                    )

        _, box_ = ui.collapsible.draw(
            box, 'object:slots', 'Slots Meshes Indices'
            )

        if box_:
            for i in range(4):
                box_.prop_search(
                    slots.meshes,
                    'mesh_{}'.format(i),
                    bpy.data,
                    'images',
                    text='Mesh {}'.format(i)
                    )

        box.operator(details.ops.XRAY_OT_pack_details_images.bl_idname)


def get_used(prefs):
    object_used = (
        # import plugins
        prefs.enable_object_import or
        prefs.enable_skls_import or
        prefs.enable_level_import or
        prefs.enable_omf_import or
        prefs.enable_ogf_import or
        # export plugins
        prefs.enable_object_export or
        prefs.enable_skls_export or
        prefs.enable_level_export or
        prefs.enable_omf_export or
        prefs.enable_ogf_export
    )
    details_used = (
        # import plugins
        prefs.enable_dm_import or
        prefs.enable_details_import or
        # export plugins
        prefs.enable_dm_export or
        prefs.enable_details_export
    )
    game_level_used = (
        # import plugins
        prefs.enable_game_level_import or
        # export plugins
        prefs.enable_game_level_export
    )
    return object_used, details_used, game_level_used


class XRAY_PT_object(ui.base.XRayPanel):
    bl_context = 'object'
    bl_label = ui.base.build_label('Object')

    @classmethod
    def poll(cls, context):
        bpy_obj = context.active_object
        if not bpy_obj:
            return False
        is_helper = utils.is_helper_object(bpy_obj)
        if is_helper:
            return False
        preferences = version_utils.get_preferences()
        object_used, details_used, game_level_used = get_used(preferences)
        return object_used or details_used or game_level_used

    def draw(self, context):
        preferences = version_utils.get_preferences()
        object_used, details_used, game_level_used = get_used(preferences)

        layout = self.layout
        data = context.object.xray
        if object_used:
            layout.prop(data, 'isroot', text='Object', toggle=True)

            if data.isroot:
                object_box = layout.box()
                if not data.flags_use_custom:
                    object_box.prop(data, 'flags_simple', text='Type')
                else:
                    row = object_box.row(align=True)
                    row.prop(data, 'flags_simple', text='Type')
                    row.prop(data, 'flags_custom_type', text='')
                    col = object_box.column(align=True)
                    row = col.row(align=True)
                    row.prop(data, 'flags_custom_progressive', text='Progressive', toggle=True)
                    row.prop(data, 'flags_custom_lod', text='LOD', toggle=True)
                    row.prop(data, 'flags_custom_hom', text='HOM', toggle=True)
                    row = col.row(align=True)
                    row.prop(data, 'flags_custom_musage', text='Multiple Usage', toggle=True)
                    row.prop(data, 'flags_custom_soccl', text='Sound Occluder', toggle=True)
                    row.prop(data, 'flags_custom_hqexp', text='HQ Export', toggle=True)
                object_box.prop(data, 'lodref')
                object_box.prop(data, 'export_path')
                row, box = ui.collapsible.draw(
                    object_box,
                    'object:userdata',
                    'User Data',
                    enabled=data.userdata != '',
                    icon='VIEWZOOM'
                )
                XRAY_OT_prop_clip.drawall(row, 'object.xray.userdata', data.userdata)
                if box:
                    if not data.userdata:
                        ui.collapsible.XRAY_OT_collaps.set_value(
                            'object:userdata',
                            False
                        )
                    else:
                        box = box.column(align=True)
                        for line in data.userdata.splitlines():
                            box.label(text=line)

                if data.motions:
                    split = object_box.split()
                    split.alert = True
                    split.prop(data, 'motions')
                _, box = ui.collapsible.draw(
                    object_box,
                    'object:motions',
                    'Motions (%d)' % len(data.motions_collection)
                )
                if box:
                    box.prop(data, 'play_active_motion', toggle=True, icon='PLAY')
                    box.prop(data, 'use_custom_motion_names', toggle=True)
                    box.prop_search(data, 'dependency_object', bpy.data, 'objects')
                    row = box.row()
                    row.template_list(
                        'XRAY_UL_motion_list', 'name',
                        data, 'motions_collection',
                        data, 'motions_collection_index',
                        rows=8
                    )
                    col = row.column(align=True)
                    ui.list_helper.draw_list_ops(
                        col,
                        data,
                        'motions_collection',
                        'motions_collection_index',
                        custom_elements_func=draw_motion_list_elements
                    )

                if data.motionrefs:
                    split = object_box.split()
                    split.alert = True
                    split.prop(data, 'motionrefs')
                _, box = ui.collapsible.draw(
                    object_box,
                    'object:motionsrefs',
                    'Motion Refs (%d)' % len(data.motionrefs_collection)
                )
                if box:
                    box.prop(data, 'load_active_motion_refs', toggle=True)
                    row = box.row()
                    row.template_list(
                        'UI_UL_list',
                        'name',
                        data,
                        'motionrefs_collection',
                        data,
                        'motionrefs_collection_index',
                        rows=6
                    )
                    col = row.column(align=True)
                    ui.list_helper.draw_list_ops(
                        col,
                        data,
                        'motionrefs_collection',
                        'motionrefs_collection_index',
                        custom_elements_func=draw_motion_refs_elements
                    )

                _, box = ui.collapsible.draw(
                    object_box,
                    'object:revision',
                    'Revision'
                )
                if box:
                    # owner
                    split = version_utils.layout_split(box, 0.35)
                    split.label(text='Owner:')
                    split.prop(data.revision, 'owner', text='')
                    # created time
                    split = version_utils.layout_split(box, 0.35)
                    split.label(text='Created Time:')
                    split.prop(data.revision, 'ctime_str', text='')
                    # time formats
                    subbox = box.box()
                    split = version_utils.layout_split(subbox, 0.25)
                    split.label(text='')
                    split.label(text='Time Formats:', icon='INFO')
                    subbox.label(text='Year.Month.Day Hours:Minutes')
                    subbox.label(text='Year.Month.Day')

        if details_used:
            layout.prop(data, 'is_details', text='Details', toggle=True)
            if data.is_details:
                details_draw_function(self, context)

        if game_level_used:
            layout.prop(data, 'is_level', text='Level', toggle=True)
            if data.is_level:
                ogf_box = layout.box()

                ogf_box.prop(data.level, 'object_type')
                object_type = data.level.object_type

                if object_type == 'LEVEL':
                    ogf_box.prop(data.level, 'source_path')

                elif object_type == 'PORTAL':
                    ogf_box.prop_search(data.level, 'sector_front', bpy.data, 'objects')
                    ogf_box.prop_search(data.level, 'sector_back', bpy.data, 'objects')

                elif object_type == 'VISUAL':
                    ogf_box.prop(data.level, 'visual_type')
                    if data.level.visual_type in {'TREE_ST', 'TREE_PM'}:
                        # color scale
                        color_scale_box = ogf_box.box()
                        color_scale_box.label(text='Color Scale:')

                        col = color_scale_box.row()
                        col.prop(data.level, 'color_scale_rgb')

                        col = color_scale_box.row()
                        col.prop(data.level, 'color_scale_hemi')

                        col = color_scale_box.row()
                        col.prop(data.level, 'color_scale_sun')

                        # color bias
                        color_bias_box = ogf_box.box()
                        color_bias_box.label(text='Color Bias:')

                        col = color_bias_box.row()
                        col.prop(data.level, 'color_bias_rgb')

                        col = color_bias_box.row()
                        col.prop(data.level, 'color_bias_hemi')

                        col = color_bias_box.row()
                        col.prop(data.level, 'color_bias_sun')

                    elif data.level.visual_type in {'NORMAL', 'PROGRESSIVE'}:
                        ogf_box.prop(data.level, 'use_fastpath')

                elif object_type == 'LIGHT_DYNAMIC':
                    ogf_box.prop(data.level, 'controller_id')
                    ogf_box.prop(data.level, 'light_type')
                    row = ogf_box.row()
                    row.prop(data.level, 'diffuse')
                    row = ogf_box.row()
                    row.prop(data.level, 'specular')
                    row = ogf_box.row()
                    row.prop(data.level, 'ambient')
                    ogf_box.prop(data.level, 'range_')
                    ogf_box.prop(data.level, 'falloff')
                    ogf_box.prop(data.level, 'attenuation_0')
                    ogf_box.prop(data.level, 'attenuation_1')
                    ogf_box.prop(data.level, 'attenuation_2')
                    ogf_box.prop(data.level, 'theta')
                    ogf_box.prop(data.level, 'phi')


classes = (
    XRAY_OT_prop_clip,
    XRAY_UL_motion_list,
    XRAY_OT_add_all_actions,
    XRAY_OT_remove_all_actions,
    XRAY_OT_clean_actions,
    XRAY_OT_copy_actions_list,
    XRAY_OT_paste_actions_list,
    XRAY_OT_remove_all_motion_refs,
    XRAY_OT_copy_motion_refs_list,
    XRAY_OT_paste_motion_refs_list,
    XRAY_PT_object
)


def register():
    version_utils.assign_props([(prop_clip_op_props, XRAY_OT_prop_clip), ])
    for clas in classes:
        bpy.utils.register_class(clas)


def unregister():
    for clas in reversed(classes):
        bpy.utils.unregister_class(clas)
