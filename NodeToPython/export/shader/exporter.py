import bpy

from ..node_group_gatherer import NodeGroupType
from ..node_tree_exporter import NodeTreeExporter
from ..ntp_operator import NTP_OT_Export
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
        obj_name: str, 
        group_type: NodeGroupType
    ):
        if group_type not in {
            NodeGroupType.LIGHT,
            NodeGroupType.LINE_STYLE,
            NodeGroupType.MATERIAL,
            NodeGroupType.SHADER_NODE_GROUP,
            NodeGroupType.WORLD
        }:
            ntp_operator.report(
                {'ERROR'},
                f"Cannot initialize ShaderExporter with group type {group_type}"
            )
        NodeTreeExporter.__init__(self, ntp_operator, obj_name, group_type)

        for name in SHADER_OP_RESERVED_NAMES:
            self._used_vars[name] = 0

    def _initialize_shader_node_tree(self, 
        ntp_node_tree: NTP_ShaderNodeTree, 
        nt_name: str
    ) -> None:
        """
        Initialize the shader node group

        Parameters:
        ntp_node_tree (NTP_ShaderNodeTree): node tree to be generated and 
            variable to use
        nt_name (str): name to use for the node tree
        """
        self._write(f"def {ntp_node_tree._var}_node_group():", 
                    self._operator._outer_indent_level)
        self._write(f'"""Initialize {nt_name} node group"""')

        is_base : bool = ntp_node_tree._node_tree == self._base_node_tree
        is_obj : bool =  self._group_type != NodeGroupType.SHADER_NODE_GROUP
        if is_base and is_obj:
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

    # NodeTreeExporter interface
    def _set_base_node_tree(self) -> None:
        match self._group_type:
            case NodeGroupType.MATERIAL:
                self._obj = bpy.data.materials[self._obj_name]
            case NodeGroupType.LIGHT:
                self._obj = bpy.data.lights[self._obj_name]
            case NodeGroupType.LINE_STYLE:
                self._obj = bpy.data.linestyles[self._obj_name]
            case NodeGroupType.WORLD:
                self._obj = bpy.data.worlds[self._obj_name]
        
        if self._group_type == NodeGroupType.SHADER_NODE_GROUP:
            self._base_node_tree = bpy.data.node_groups[self._obj_name]
        else:
            self._base_node_tree = self._obj.node_tree

        if self._base_node_tree is None:
            self._operator.report(
                {'ERROR'}, 
                ("NodeToPython: Couldn't find base node tree")
            )

    def _initialize_ntp_node_tree(
        self, 
        node_tree: bpy.types.NodeTree,
        nt_var: str
    ) -> NTP_NodeTree:
        return NTP_ShaderNodeTree(node_tree, nt_var)

    # NodeTreeExporter interface    
    def _create_obj(self):
        match self._group_type:
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
        self._write(f"def {ntp_node_tree._var}_node_group():", 
                    self._operator._outer_indent_level)
        self._write(f'"""Initialize {nt_name} node group"""')

        is_tree_base : bool = ntp_node_tree._node_tree == self._base_node_tree
        is_obj : bool =  self._group_type != NodeGroupType.SHADER_NODE_GROUP
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
        
        self._write(f"{self._obj_var} = bpy.data.materials.new("
                    f"name = {str_to_py_str(self._obj_name)})", indent_level)
        self._write("if bpy.app.version < (5, 0, 0):", indent_level)
        self._write(f"{self._obj_var}.use_nodes = True\n\n", indent_level + 1)

        #TODO: other material settings
    
    def _create_light(self):
        indent_level = self._get_obj_creation_indent()
        
        self._write(
            f"{self._obj_var} = bpy.data.lights.new("
            f"name = {str_to_py_str(self._obj_name)}, "
            f"type = {enum_to_py_str(self._obj.type)})",
            indent_level
        )
        self._write(f"{self._obj_var}.use_nodes = True\n\n", indent_level)
        self._write(
            f"{LIGHT_OBJ} = bpy.data.objects.new("
            f"name = {str_to_py_str(self._obj.name)}, "
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

        self._write(f"{self._obj_var} = bpy.data.linestyles.new("
                    f"name = {str_to_py_str(self._obj_name)})", indent_level)
        self._write(f"{self._obj_var}.use_nodes = True\n", indent_level)

    def _create_world(self):
        indent_level = self._get_obj_creation_indent()
        
        self._write(f"{self._obj_var} = bpy.data.worlds.new("
                    f"name = {str_to_py_str(self._obj_name)})", indent_level)
        self._write("if bpy.app.version < (5, 0, 0):", indent_level)
        self._write(f"{self._obj_var}.use_nodes = True\n\n", indent_level + 1)