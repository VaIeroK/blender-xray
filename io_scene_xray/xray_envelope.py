# addon modules
from . import log
from . import motion_utils
from . import text
from . import xray_io
from . import xray_interpolation
from . import xray_motions


@log.with_context('envelope')
def import_envelope(reader, ver, fcurve, fps, koef, name, warn_list, unique_shapes):
    bhv_fmt = 'I'
    if ver > 3:
        bhv_fmt = 'B'
    bhv0, bhv1 = map(xray_interpolation.Behavior, reader.getf('<2' + bhv_fmt))

    if bhv0 != bhv1:
        log.warn(
            text.warn.envelope_behaviors_replaced,
            behavior=bhv1.name,
            replacement=bhv0.name
        )
        bhv1 = bhv0
    if bhv0 == xray_interpolation.Behavior.CONSTANT:
        fcurve.extrapolation = 'CONSTANT'
    elif bhv0 == xray_interpolation.Behavior.LINEAR:
        fcurve.extrapolation = 'LINEAR'
    else:
        bhv1 = xray_interpolation.Behavior.CONSTANT
        log.warn(
            text.warn.envelope_bad_behavior,
            behavior=bhv0.name,
            replacement=bhv1.name
        )
        bhv0 = bhv1
        fcurve.extrapolation = 'CONSTANT'

    replace_unsupported_to = 'BEZIER'
    unsupported_occured = set()
    fckf = fcurve.keyframe_points
    use_interpolate = False
    values = []
    times = []
    shapes = []
    tcb = []
    params = []
    count_fmt = 'I'
    if ver > 3:
        count_fmt = 'H'
    keyframes_count = reader.getf('<' + count_fmt)[0]
    if ver > 3:
        for _ in range(keyframes_count):
            value = reader.getf('<f')[0]
            time = reader.getf('<f')[0] * fps
            shape = xray_interpolation.Shape(reader.getf('<B')[0])
            if shape != xray_interpolation.Shape.STEPPED:
                tension = reader.getq16f(-32.0, 32.0)
                continuity = reader.getq16f(-32.0, 32.0)
                bias = reader.getq16f(-32.0, 32.0)
                param = []
                for param_index in range(4):
                    param_value = reader.getq16f(-32.0, 32.0)
                    param.append(param_value)
            else:
                tension = 0.0
                continuity = 0.0
                bias = 0.0
                param = (0.0, 0.0, 0.0, 0.0)
            values.append(value)
            times.append(time)
            shapes.append(shape)
            tcb.append((tension, continuity, bias))
            params.append(param)
            if not shape in (
                    xray_interpolation.Shape.TCB,
                    xray_interpolation.Shape.HERMITE,
                    xray_interpolation.Shape.BEZIER_1D,
                    xray_interpolation.Shape.LINEAR,
                    xray_interpolation.Shape.STEPPED,
                    xray_interpolation.Shape.BEZIER_2D
                ):
                unsupported_occured.add(shape.name)
            unique_shapes.add(shape.name)
            if shape in (
                    xray_interpolation.Shape.TCB,
                    xray_interpolation.Shape.HERMITE,
                    xray_interpolation.Shape.BEZIER_1D,
                    xray_interpolation.Shape.BEZIER_2D
                ):
                use_interpolate = True
    else:
        for _ in range(keyframes_count):
            value = reader.getf('<f')[0]
            time = reader.getf('<f')[0] * fps
            shape = xray_interpolation.Shape(reader.getf('<I')[0] & 0xff)
            tension, continuity, bias = reader.getf('<3f')
            param = reader.getf('<4f')    # params
            values.append(value)
            times.append(time)
            shapes.append(shape)
            tcb.append((tension, continuity, bias))
            params.append(param)
            if not shape in (
                    xray_interpolation.Shape.TCB,
                    xray_interpolation.Shape.HERMITE,
                    xray_interpolation.Shape.BEZIER_1D,
                    xray_interpolation.Shape.LINEAR,
                    xray_interpolation.Shape.STEPPED,
                    xray_interpolation.Shape.BEZIER_2D
                ):
                unsupported_occured.add(shape.name)
            unique_shapes.add(shape.name)
            if shape in (
                    xray_interpolation.Shape.TCB,
                    xray_interpolation.Shape.HERMITE,
                    xray_interpolation.Shape.BEZIER_1D,
                    xray_interpolation.Shape.BEZIER_2D
                ):
                use_interpolate = True
    if use_interpolate:
        start_frame = int(round(times[0], 0))
        end_frame = int(round(times[-1], 0))
        values, times = xray_motions.interpolate_keys(
            fps, start_frame, end_frame, values, times, shapes, tcb, params
        )
        for time, value in zip(times, values):
            key_frame = fckf.insert(time, value * koef)
            key_frame.interpolation = 'LINEAR'
    else:
        key_count = len(times)
        for index, (time, value, shape_prev) in enumerate(zip(times, values, shapes)):
            key_frame = fckf.insert(time, value * koef)
            if index + 1 < key_count:
                shape = shapes[index + 1]
            else:
                shape = shapes[-1]
            if shape == xray_interpolation.Shape.LINEAR:
                key_frame.interpolation = 'LINEAR'
            elif shape == xray_interpolation.Shape.STEPPED:
                key_frame.interpolation = 'CONSTANT'
            else:
                key_frame.interpolation = replace_unsupported_to

    if unsupported_occured:
        warn_list.append((
            tuple(unsupported_occured),
            replace_unsupported_to,
            name
        ))

    return use_interpolate


@log.with_context('envelope')
def export_envelope(writer, ver, fcurve, fps, koef, epsilon=motion_utils.EPSILON):
    behavior = None
    if fcurve.extrapolation == 'CONSTANT':
        behavior = xray_interpolation.Behavior.CONSTANT
    elif fcurve.extrapolation == 'LINEAR':
        behavior = xray_interpolation.Behavior.LINEAR
    else:
        behavior = xray_interpolation.Behavior.LINEAR
        log.warn(
            text.warn.envelope_extrapolation,
            extrapolation=fcurve.extrapolation,
            replacement=behavior.name
        )
    behav_fmt = 'I'
    if ver > 3:
        behav_fmt = 'B'
    writer.putf('<2' + behav_fmt, behavior.value, behavior.value)

    replace_unsupported_to = xray_interpolation.Shape.TCB
    unsupported_occured = set()

    def generate_keys(keyframe_points):
        prev_kf = None
        for curr_kf in keyframe_points:
            shape = xray_interpolation.Shape.STEPPED
            if prev_kf is not None:
                if prev_kf.interpolation == 'CONSTANT':
                    shape = xray_interpolation.Shape.STEPPED
                elif prev_kf.interpolation == 'LINEAR':
                    shape = xray_interpolation.Shape.LINEAR
                else:
                    unsupported_occured.add(prev_kf.interpolation)
                    shape = replace_unsupported_to
            prev_kf = curr_kf
            yield motion_utils.KF(curr_kf.co.x / fps, curr_kf.co.y / koef, shape)

    kf_writer = xray_io.PackedWriter()
    keyframes = motion_utils.refine_keys(generate_keys(fcurve.keyframe_points), epsilon)
    count = motion_utils.export_keyframes(kf_writer, keyframes, anm_ver=ver)

    count_fmt = 'I'
    if ver > 3:
        count_fmt = 'H'
    writer.putf('<' + count_fmt, count)
    writer.putp(kf_writer)

    if unsupported_occured:
        log.warn(
            text.warn.envelope_shapes,
            shapes=unsupported_occured,
            replacement=replace_unsupported_to.name
        )
