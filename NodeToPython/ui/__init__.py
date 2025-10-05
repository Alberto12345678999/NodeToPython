if "bpy" in locals():
    import importlib
    importlib.reload(main)
    importlib.reload(settings)
    importlib.reload(generation_settings)
    importlib.reload(addon_settings)
else:
    from . import main
    from . import settings
    from . import generation_settings
    from . import addon_settings

import bpy

modules = [
    main,
    settings,
    generation_settings,
    addon_settings
]