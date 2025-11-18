import bpy

from . import main
from ..export.ntp_options import NTP_PG_Options

class NTP_PT_Settings(bpy.types.Panel):
    bl_idname = "NTP_PT_settings"
    bl_label = "Settings"
    bl_parent_id = main.NTP_PT_Main.bl_idname
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = "NodeToPython"
    bl_description = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    @classmethod
    def poll(cls, context):
        return True
    
    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        ntp_options : NTP_PG_Options = getattr(context.scene, "ntp_options")

        option_list = [
            "mode"
        ]
        for option in option_list:
            layout.prop(ntp_options, option)

classes: list[type] = [
    NTP_PT_Settings
]