import bpy

from ..export.node_group_gatherer import NodeGroupGatherer
from ..export.ntp_operator import NTP_OT_Export
from ..export.ntp_options import NTP_PG_Options

import pathlib

class NTP_PT_Main(bpy.types.Panel):
    bl_idname = "NTP_PT_main"
    bl_label = "Node To Python"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = "NodeToPython"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    @classmethod
    def poll(cls, context):
        return True
    
    def draw_header(self, context):
        layout = self.layout

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        col = layout.column(align=True)
        row = col.row()

        ntp_options : NTP_PG_Options = getattr(context.scene, "ntp_options")
        location = ""
        export_icon = ''
        if ntp_options.mode == 'SCRIPT':
            location = "clipboard"
            export_icon = 'COPYDOWN'
        else: # mode == 'ADDON'
            location = f"{pathlib.PurePath(ntp_options.dir_path).name}/"
            export_icon = 'FILE_FOLDER'

        gatherer = NodeGroupGatherer()
        gatherer.gather_node_groups(context)
        num_node_groups = gatherer.get_number_node_groups()

        if num_node_groups == 1:
            node_group = gatherer.get_single_node_group()[1].name
        else:
            node_group = f"{num_node_groups} node groups"

        export_text = f"Export {node_group} to {location}"

        if location == "":
            export_text = "Add a save location to get started!"
            export_icon = 'ERROR'

        if num_node_groups == 0:
            export_text = "Add a node group to get started!"
            export_icon = 'ERROR'

        export_button = row.operator(
            NTP_OT_Export.bl_idname, 
            text=export_text, 
            icon=export_icon
        )
        row.enabled = num_node_groups > 0 and location != ""

classes: list[type] = [
    NTP_PT_Main
]