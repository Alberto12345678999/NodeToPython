import bpy

from ..ntp_node_tree import NTP_NodeTree

class NTP_GeoNodeTree(NTP_NodeTree):
    def __init__(self, node_tree: bpy.types.GeometryNodeTree, var: str):
        super().__init__(node_tree, var)
        if bpy.app.version >= (3, 6, 0):
            self._zone_inputs["GeometryNodeSimulationInput"] = []
        if bpy.app.version >= (4, 0, 0):
            self._zone_inputs["GeometryNodeRepeatInput"] = []
        if bpy.app.version >= (4, 3, 0):
            self._zone_inputs["GeometryNodeForeachGeometryElementInput"] = []
        if bpy.app.version >= (5, 0, 0):
            self._zone_inputs["NodeClosureInput"] = []
