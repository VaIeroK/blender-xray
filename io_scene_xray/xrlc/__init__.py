# addon modules
from . import ops


modules = (
    ops,
)


def register():
    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()
