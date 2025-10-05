bl_info = {
    "name": "Node to Python", 
    "description": "Convert Blender node groups to a Python add-on!",
    "author": "Brendan Parmer",
    "version": (3, 5, 1),
    "blender": (3, 0, 0),
    "location": "Node", 
    "category": "Node",
}

if "bpy" in locals():
    import importlib
    importlib.reload(export_operator)
    importlib.reload(ntp_options)
    importlib.reload(ui)
    importlib.reload(compositor)
    importlib.reload(geometry)
    importlib.reload(shader)
else:
    from . import export_operator
    from . import ntp_options
    from . import ui
    from . import compositor
    from . import geometry
    from . import shader
import bpy

modules = [export_operator, ntp_options]
for parent_module in [ui, compositor, geometry, shader]:
    if hasattr(parent_module, "modules"):
        modules += parent_module.modules
    else:
        raise Exception(f"Module {parent_module} does not have list of modules")

def register():
    for module in modules:
        if hasattr(module, "classes"):
            for cls in getattr(module, "classes"):
                bpy.utils.register_class(cls)
        if hasattr(module, "register_props"):
            getattr(module, "register_props")()

def unregister():
    for module in modules:
        if hasattr(module, "classes"):
            for cls in getattr(module, "classes"):
                bpy.utils.unregister_class(cls)
        if hasattr(module, "unregister_props"):
            getattr(module, "unregister_props")()

if __name__ == "__main__":
    register()