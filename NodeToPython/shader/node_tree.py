import bpy

from ..ntp_node_tree import NTP_NodeTree

class NTP_ShaderNodeTree(NTP_NodeTree):
    def __init__(self, node_tree: bpy.types.ShaderNodeTree, var: str):
        super().__init__(node_tree, var)
        self.zone_inputs: dict[str, list[bpy.types.Node]] = {}
        if bpy.app.version >= (5, 0, 0):
            self.zone_inputs["GeometryNodeRepeatInput"] = []
            self.zone_inputs["NodeClosureInput"] = []
