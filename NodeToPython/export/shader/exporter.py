import bpy

from ..node_group_gatherer import NodeGroupType
from ..node_tree_exporter import NodeTreeExporter, NODE_TREE_NAMES
from ..ntp_operator import NTP_OT_Export, NodeTreeInfo
from ..utils import *

from .node_tree import NTP_ShaderNodeTree, NTP_NodeTree

NODE = "node"
LIGHT_OBJ = "light_obj"
SHADER_OP_RESERVED_NAMES = {
    NODE, 
    LIGHT_OBJ
}

class ShaderExporter(NodeTreeExporter):
    def __init__(
        self, 
        ntp_operator: NTP_OT_Export,
        node_tree_info: NodeTreeInfo
    ):
        if not node_tree_info._group_type.is_shader():
            ntp_operator.report(
                {'ERROR'},
                f"Cannot initialize ShaderExporter with group type "
                f"{node_tree_info._group_type}"
            )
        NodeTreeExporter.__init__(self, ntp_operator, node_tree_info)

        for name in SHADER_OP_RESERVED_NAMES:
            self._used_vars[name] = 0

    def _initialize_ntp_node_tree(
        self, 
        node_tree: bpy.types.NodeTree,
        nt_var: str
    ) -> NTP_NodeTree:
        return NTP_ShaderNodeTree(node_tree, nt_var)

    # NodeTreeExporter interface    
    def _create_obj(self):
        match self._node_tree_info._group_type:
            case NodeGroupType.MATERIAL:
                self._create_material()
            case NodeGroupType.LIGHT:
                self._create_light()
            case NodeGroupType.LINE_STYLE:
                self._create_line_style()
            case NodeGroupType.WORLD:
                self._create_world()

    # NodeTreeExporter interface
    def _initialize_node_tree(self, ntp_node_tree: NTP_NodeTree) -> None:
        nt_name = ntp_node_tree._node_tree.name
        self._node_tree_info._func = f"{ntp_node_tree._var}_node_group"
        #initialize node group
        self._write(f"def {self._node_tree_info._func}("
                    f"{NODE_TREE_NAMES}: dict[typing.Callable, str]):", 
                    self._operator._outer_indent_level)
        self._write(f'"""Initialize {nt_name} node group"""')

        is_tree_base : bool = ntp_node_tree._node_tree == self._base_node_tree
        is_obj : bool =  self._node_tree_info._group_type.is_obj()
        if is_tree_base and is_obj:
            self._write(f"{ntp_node_tree._var} = {self._obj_var}.node_tree\n")
            self._write(f"# Start with a clean node tree")
            self._write(f"for {NODE} in {ntp_node_tree._var}.nodes:")
            self._write(f"{ntp_node_tree._var}.nodes.remove({NODE})", 
                        self._operator._inner_indent_level + 1)
        else:
            self._write((f"{ntp_node_tree._var} = bpy.data.node_groups.new("
                         f"type = \'ShaderNodeTree\', "
                         f"name = {str_to_py_str(nt_name)})"))
            self._write("", 0)
    
    def _create_material(self):
        indent_level = self._get_obj_creation_indent()
        
        self._write(
            f"{self._obj_var} = bpy.data.materials.new("
            f"name = {str_to_py_str(self._node_tree_info._obj.name)})", 
            indent_level
        )
        self._write("if bpy.app.version < (5, 0, 0):", indent_level)
        self._write(f"{self._obj_var}.use_nodes = True\n\n", indent_level + 1)

        #TODO: other material settings
    
    def _create_light(self):
        indent_level = self._get_obj_creation_indent()
        
        light_type = getattr(self._node_tree_info._obj, "type")
        self._write(
            f"{self._obj_var} = bpy.data.lights.new("
            f"name = {str_to_py_str(self._node_tree_info._obj.name)}, "
            f"type = {enum_to_py_str(light_type)})",
            indent_level
        )
        self._write(f"{self._obj_var}.use_nodes = True\n\n", indent_level)
        self._write(
            f"{LIGHT_OBJ} = bpy.data.objects.new("
            f"name = {str_to_py_str(self._node_tree_info._obj.name)}, "
            f"object_data={self._obj_var})",
            indent_level
        )
        self._write(
            f"bpy.context.collection.objects.link({LIGHT_OBJ})", 
            indent_level
        )
        #TODO: other light settings
        
        self._write("", 0)

    def _create_line_style(self):
        indent_level = self._get_obj_creation_indent()

        self._write(
            f"{self._obj_var} = bpy.data.linestyles.new("
            f"name = {str_to_py_str(self._node_tree_info._obj.name)})", 
            indent_level
        )
        self._write(f"{self._obj_var}.use_nodes = True\n", indent_level)
        # TODO: other line style settings

    def _create_world(self):
        indent_level = self._get_obj_creation_indent()
        
        self._write(
            f"{self._obj_var} = bpy.data.worlds.new("
            f"name = {str_to_py_str(self._node_tree_info._obj.name)})", 
            indent_level
        )
        self._write("if bpy.app.version < (5, 0, 0):", indent_level)
        self._write(f"{self._obj_var}.use_nodes = True\n\n", indent_level + 1)
        # TODO: other world settings