from .. import xray_io
from ..ogf import imp


def import_hierrarhy_visuals(level):
    for hierrarhy_visual in level.hierrarhy_visuals:
        for child_index in hierrarhy_visual.children:
            hierrarhy_obj = level.visuals[hierrarhy_visual.index]
            child_obj = level.visuals[child_index]
            if hierrarhy_visual.visual_type == 'LOD':
                hierrarhy_obj.location = child_obj.location
                hierrarhy_obj.rotation_euler = child_obj.rotation_euler
                hierrarhy_obj.scale = child_obj.scale
                child_obj.location = (0, 0, 0)
                child_obj.rotation_euler = (0, 0, 0)
                child_obj.scale = (1, 1, 1)
            child_obj.parent = hierrarhy_obj


def import_visuals(data, level):
    chunked_reader = xray_io.ChunkedReader(data)

    chunks = set()
    visuals_ids = set()
    for visual_id, visual_data in chunked_reader:
        visuals_ids.add(visual_id)
        imp.import_(visual_data, visual_id, level, chunks, visuals_ids)
    chunks = list(chunks)
    chunks.sort()
    for i in chunks:
        print(i)
