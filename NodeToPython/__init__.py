if "bpy" in locals():
    import importlib
    importlib.reload(export)
    importlib.reload(ui)
else:
    from . import export
    from . import ui
import bpy

modules = []
for parent_module in [export, ui]:
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