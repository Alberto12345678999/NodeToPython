import bpy

from . import settings
from ..export.ntp_options import NTP_PG_Options

class NTP_PT_AddonSettings(bpy.types.Panel):
    bl_idname = "NTP_PT_addon_settings"
    bl_label = "Add-on Settings"
    bl_parent_id = settings.NTP_PT_Settings.bl_idname
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = "NodeToPython"
    bl_description = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    @classmethod
    def poll(cls, context):
        options: NTP_PG_Options = getattr(context.scene, "ntp_options")
        return options.mode == 'ADDON'
    
    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        ntp_options : NTP_PG_Options = getattr(context.scene, "ntp_options")

        addon_options = [
            "dir_path",
            "name",
            "description",
            "author_name",
            "version",
            "location",
            "menu_id",
            "license",
            "should_create_license",
            "category"
        ]
        if ntp_options.category == 'Custom':
            addon_options.append("custom_category")
        for option in addon_options:
            layout.prop(ntp_options, option)

classes: list[type] = [
    NTP_PT_AddonSettings
]