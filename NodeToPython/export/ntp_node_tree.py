import bpy

class NTP_NodeTree:
    def __init__(self, node_tree: bpy.types.NodeTree, var: str):
        # Blender node tree object being copied
        self._node_tree: bpy.types.NodeTree = node_tree

        # The variable named for the regenerated node tree
        self._var: str = var

        self._zone_inputs: dict[str, list[bpy.types.Node]] = {}

        if bpy.app.version < (4, 0, 0):
            # Keep track of if we need to set the default values for the node
            # tree inputs and outputs
            self.inputs_set: bool = False
            self.outputs_set: bool = False