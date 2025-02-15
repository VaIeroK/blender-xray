# addon modules
from . import base
from . import collapsible
from . import dynamic_menu
from . import edit_helper
from . import list_helper
from . import motion_list


modules = (
    collapsible,
    dynamic_menu,
    edit_helper,
    list_helper,
    motion_list,
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
