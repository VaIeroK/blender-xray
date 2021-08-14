# blender modules
import bpy

# addon modules
from .. import ui
from .. import ops
from .. import version_utils
from .. import props


class XRAY_PT_ArmaturePanel(ui.base.XRayPanel):
    bl_context = 'data'
    bl_label = ui.base.build_label('Skeleton')

    @classmethod
    def poll(cls, context):
        preferences = version_utils.get_preferences()
        panel_used = (
            # import plugins
            preferences.enable_object_import or
            preferences.enable_skls_import or
            preferences.enable_bones_import or
            preferences.enable_omf_import or
            # export plugins
            preferences.enable_object_export or
            preferences.enable_skls_export or
            preferences.enable_bones_export or
            preferences.enable_omf_export or
            preferences.enable_ogf_export
        )
        return (
            context.active_object and
            context.active_object.type == 'ARMATURE' and
            panel_used
        )

    def draw(self, context):
        layout = self.layout
        data = context.active_object.data.xray
        verdif = data.check_different_version_bones()
        if verdif != 0:
            layout.label(
                text='Found bones, edited with '
                + props.bone.ShapeProperties.fmt_version_different(verdif)
                + ' version of this plugin',
                icon='ERROR'
            )
        layout.prop(data, 'display_bone_shapes', toggle=True)
        col = layout.column(align=True)
        col.prop(data, 'display_bone_mass_centers', toggle=True)
        row = col.row(align=True)
        row.active = data.display_bone_mass_centers
        row.prop(data, 'bone_mass_center_cross_size')

        # joint limits
        row, box = ui.collapsible.draw(
            layout,
            'armature:joint_limits',
            'Joint Limits'
        )
        if box:
            split = version_utils.layout_split(box, 0.5)
            split.label(text='Export Limits from:')
            split.prop(data, 'joint_limits_type', text='')
            col = box.column(align=True)
            col.prop(data, 'display_bone_limits', toggle=True)
            column = col.column(align=True)
            column.active = data.display_bone_limits
            column.prop(data, 'display_bone_limits_radius')
            row = column.row(align=True)
            row.prop(data, 'display_bone_limit_x', toggle=True)
            row.prop(data, 'display_bone_limit_y', toggle=True)
            row.prop(data, 'display_bone_limit_z', toggle=True)
            col = box.column(align=True)
            col.operator(
                ops.joint_limits.XRAY_OT_ConvertJointLimitsToConstraints.bl_idname,
                icon='CONSTRAINT_BONE'
            )
            col.operator(
                ops.joint_limits.XRAY_OT_RemoveJointLimitsConstraints.bl_idname,
                icon='X'
            )
            col.operator(
                ops.joint_limits.XRAY_OT_ConvertIKLimitsToXRayLimits.bl_idname
            )
            col.operator(
                ops.joint_limits.XRAY_OT_ConvertXRayLimitsToIKLimits.bl_idname
            )
            col.operator(
                ops.joint_limits.XRAY_OT_ClearIKLimits.bl_idname
            )

        # fake bones
        row, box = ui.collapsible.draw(
            layout,
            'armature:fake_bones',
            'Fake Bones'
        )
        if box:
            lay = box.column(align=True)
            row = lay.row(align=True)
            row.operator(ops.fake_bones.XRAY_OT_CreateFakeBones.bl_idname, text='Create', icon='CONSTRAINT_BONE')
            row.operator(ops.fake_bones.XRAY_OT_DeleteFakeBones.bl_idname, text='Delete', icon='X')
            lay.operator(
                ops.fake_bones.XRAY_OT_ToggleFakeBonesVisibility.bl_idname,
                text='Show/Hide',
                icon=version_utils.get_icon('VISIBLE_IPO_ON'),
            )

        # fake bones
        row, box = ui.collapsible.draw(
            layout,
            'armature:link_or_unlink_bones',
            'Link/Unlink Bones'
        )
        if box:
            box.prop_search(data, 'link_to_armature', bpy.data, 'objects', text='')
            column = box.column(align=True)
            column.operator('io_scene_xray.link_bones')
            column.operator('io_scene_xray.unlink_bones')


def register():
    bpy.utils.register_class(XRAY_PT_ArmaturePanel)


def unregister():
    bpy.utils.unregister_class(XRAY_PT_ArmaturePanel)
