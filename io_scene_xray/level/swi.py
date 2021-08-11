# addon modules
from .. import xray_io


class SlideWindowItem(object):
    def __init__(self, offset, triangles_count, vertices_count):
        self.offset = offset
        self.triangles_count = triangles_count
        self.vertices_count = vertices_count


def import_slide_window_item(packed_reader):
    reserved = packed_reader.getf('4I')
    slide_window_count = packed_reader.getf('I')[0]
    swis = []

    for slide_window_index in range(slide_window_count):
        offset = packed_reader.getf('I')[0]
        triangles_count = packed_reader.getf('H')[0]
        vertices_count = packed_reader.getf('H')[0]

        swi = SlideWindowItem(offset, triangles_count, vertices_count)
        swis.append(swi)

    return swis


def import_slide_window_items(data):
    packed_reader = xray_io.PackedReader(data)
    swis_count = packed_reader.getf('I')[0]
    swis_buffer = []

    for swi_index in range(swis_count):
        swis = import_slide_window_item(packed_reader)
        swis_buffer.append(swis)

    return swis_buffer
