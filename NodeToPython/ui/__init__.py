if "bpy" in locals():
    import importlib
    importlib.reload(main)
    importlib.reload(settings)
    importlib.reload(generation_settings)
    importlib.reload(addon_settings)
    importlib.reload(compositor)
    importlib.reload(geometry)
    importlib.reload(shader)
else:
    from . import main
    from . import settings
    from . import generation_settings
    from . import addon_settings
    from . import compositor
    from . import geometry
    from . import shader

import bpy

modules = [
    main,
    settings,
    generation_settings,
    addon_settings
]
modules += compositor.modules
modules += geometry.modules
modules += shader.modules