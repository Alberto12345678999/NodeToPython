import bpy

from . import settings
from ..export.ntp_options import NTP_PG_Options

class NTP_PT_GenerationSettings(bpy.types.Panel):
    bl_idname = "NTP_PT_generation_settings"
    bl_label = "Generation Settings"
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
        return True
    
    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        ntp_options : NTP_PG_Options = getattr(context.scene, "ntp_options")

        generation_options = [
            "set_group_defaults",
            "set_node_sizes", 
            "indentation_type",
            "link_external_node_groups"
        ]
        generation_options.append("set_unavailable_defaults")

        if ntp_options.mode == 'SCRIPT':
            script_options = [
                "include_imports"
            ]
            generation_options += script_options
            
        for option in generation_options:
            layout.prop(ntp_options, option)

classes: list[type] = [
    NTP_PT_GenerationSettings
]