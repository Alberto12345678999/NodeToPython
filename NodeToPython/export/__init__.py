if "bpy" in locals():
    import importlib
    importlib.reload(license_templates)
    importlib.reload(node_group_gatherer)
    importlib.reload(node_settings)
    importlib.reload(node_tree_exporter)
    importlib.reload(ntp_operator)
    importlib.reload(ntp_options)
    importlib.reload(utils)
    importlib.reload(compositor)
    importlib.reload(geometry)
    importlib.reload(shader)
else:
    from . import license_templates
    from . import node_group_gatherer
    from . import node_settings
    from . import node_tree_exporter
    from . import ntp_operator
    from . import ntp_options
    from . import utils
    from . import compositor
    from . import geometry
    from . import shader

import bpy

modules = [
    ntp_options,
    ntp_operator
]