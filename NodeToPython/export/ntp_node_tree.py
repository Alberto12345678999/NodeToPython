import bpy

class NTP_NodeTree:
    def __init__(self, node_tree: bpy.types.NodeTree, var: str):
        # Blender node tree object being copied
        self._node_tree: bpy.types.NodeTree = node_tree

        # The variable named for the regenerated node tree
        self._var: str = var

        self._zone_inputs: dict[str, list[bpy.types.Node]] = {}