if "bpy" in locals():
    import importlib
    importlib.reload(exporter)
else:
    from . import exporter

import bpy

modules = [
    exporter
]