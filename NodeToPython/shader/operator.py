import bpy
from bpy.types import Node
from bpy.types import ShaderNodeTree

from io import StringIO

from ..utils import *
from ..ntp_operator import NTP_Operator
from .node_tree import NTP_ShaderNodeTree
from ..node_settings import node_settings

NODE = "node"
LIGHT_OBJ = "light_obj"
SHADER_OP_RESERVED_NAMES = {NODE, LIGHT_OBJ}

class NTP_OT_Shader(NTP_Operator):
    bl_idname = "ntp.shader"
    bl_label =  "Shader to Python"
    bl_options = {'REGISTER', 'UNDO'}
    
    name: bpy.props.StringProperty(name="Node Group")
    group_type : bpy.props.EnumProperty(
        name = "Group Type",
        items=[
            ('MATERIAL', "Material", "Material"),
            ('NODE_GROUP', "Node Group", "Node group (typically a sub-group of a graph)"),
            ('LIGHT', "Light", "Light"),
            ('LINE_STYLE', "Line Style", "Line Style"),
            ('WORLD', "World", "World")
        ]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._node_infos = node_settings
        self.obj_var : str = ""
        self.obj : (
            bpy.types.Material |
            bpy.types.Light |
            bpy.types.FreestyleLineStyle |
            bpy.types.World |
            None
        ) = None
        for name in SHADER_OP_RESERVED_NAMES:
            self._used_vars[name] = 0
    
    def _create_material(self):
        indent_level: int = 0
        if self._mode == 'ADDON':
            indent_level = 2
        elif self._mode == 'SCRIPT':
            indent_level = 0
        
        self._write(f"{self.obj_var} = bpy.data.materials.new("
                    f"name = {str_to_py_str(self.name)})", indent_level)
        self._write("if bpy.app.version < (5, 0, 0):", indent_level)
        self._write(f"{self.obj_var}.use_nodes = True\n\n", indent_level + 1)

        #TODO: other material settings
    
    def _create_light(self):
        indent_level: int = 0
        if self._mode == 'ADDON':
            indent_level = 2
        elif self._mode == 'SCRIPT':
            indent_level = 0
        
        self._write(
            f"{self.obj_var} = bpy.data.lights.new("
            f"name = {str_to_py_str(self.name)}, "
            f"type = {enum_to_py_str(self.obj.type)})",
            indent_level
        )
        self._write(f"{self.obj_var}.use_nodes = True\n\n", indent_level)
        self._write(
            f"{LIGHT_OBJ} = bpy.data.objects.new("
            f"name = {str_to_py_str(self.obj.name)}, "
            f"object_data={self.obj_var})",
            indent_level
        )
        self._write(
            f"bpy.context.collection.objects.link({LIGHT_OBJ})", 
            indent_level
        )
        #TODO: other light settings
        
        self._write("", 0)

    def _create_line_style(self):
        indent_level: int = 0
        if self._mode == 'ADDON':
            indent_level = 2
        elif self._mode == 'SCRIPT':
            indent_level = 0
        
        self._write(f"{self.obj_var} = bpy.data.linestyles.new("
                    f"name = {str_to_py_str(self.name)})", indent_level)
        self._write(f"{self.obj_var}.use_nodes = True\n", indent_level)

    def _create_world(self):
        indent_level: int = 0
        if self._mode == 'ADDON':
            indent_level = 2
        elif self._mode == 'SCRIPT':
            indent_level = 0
        
        self._write(f"{self.obj_var} = bpy.data.worlds.new("
                    f"name = {str_to_py_str(self.name)})", indent_level)
        self._write("if bpy.app.version < (5, 0, 0):", indent_level)
        self._write(f"{self.obj_var}.use_nodes = True\n\n", indent_level + 1)

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
        self._write(f"def {ntp_node_tree.var}_node_group():", self._outer_indent_level)
        self._write(f'"""Initialize {nt_name} node group"""')

        is_base : bool = ntp_node_tree.node_tree == self._base_node_tree
        is_obj : bool =  self.group_type != 'NODE_GROUP'
        if is_base and is_obj:
            self._write(f"{ntp_node_tree.var} = {self.obj_var}.node_tree\n")
            self._write(f"# Start with a clean node tree")
            self._write(f"for {NODE} in {ntp_node_tree.var}.nodes:")
            self._write(f"{ntp_node_tree.var}.nodes.remove({NODE})", self._inner_indent_level + 1)
        else:
            self._write((f"{ntp_node_tree.var} = bpy.data.node_groups.new("
                         f"type = \'ShaderNodeTree\', "
                         f"name = {str_to_py_str(nt_name)})"))
            self._write("", 0)

    def _process_node(self, node: Node, ntp_nt: NTP_ShaderNodeTree) -> None:
        """
        Create node and set settings, defaults, and cosmetics

        Parameters:
        node (Node): node to process
        ntp_nt (NTP_ShaderNodeTree): the node tree that node belongs to
        """
        node_var: str = self._create_node(node, ntp_nt.var)
        self._set_settings_defaults(node)
        
        if bpy.app.version < (4, 0, 0):
            if node.bl_idname == 'NodeGroupInput' and not ntp_nt.inputs_set:
                self._group_io_settings(node, "input", ntp_nt)
                ntp_nt.inputs_set = True

            elif node.bl_idname == 'NodeGroupOutput' and not ntp_nt.outputs_set:
                self._group_io_settings(node, "output", ntp_nt)
                ntp_nt.outputs_set = True
        
        if node.bl_idname in ntp_nt.zone_inputs:
            ntp_nt.zone_inputs[node.bl_idname].append(node)

        self._hide_hidden_sockets(node)
        if node.bl_idname not in ntp_nt.zone_inputs:
            self._set_socket_defaults(node)

    if bpy.app.version >= (5, 0, 0):
        def _process_zones(self, zone_input_list: list[bpy.types.Node]) -> None:
            """
            Recreates a zone
            zone_input_list (list[bpy.types.Node]): list of zone input 
                nodes
            """
            for input_node in zone_input_list:
                zone_output = input_node.paired_output

                zone_input_var = self._node_vars[input_node]
                zone_output_var = self._node_vars[zone_output]

                self._write(f"# Process zone input {input_node.name}")
                self._write(f"{zone_input_var}.pair_with_output"
                            f"({zone_output_var})")

                #must set defaults after paired with output
                self._set_socket_defaults(input_node)
                self._set_socket_defaults(zone_output)

            if zone_input_list:
                self._write("", 0)

    def _process_node_tree(self, node_tree: ShaderNodeTree) -> None:
        """
        Generates a Python function to recreate a node tree

        Parameters:
        node_tree (NodeTree): node tree to be recreated
        level (int): number of tabs to use for each line, used with
            node groups within node groups and script/add-on differences
        """

        nt_var = self._create_var(node_tree.name)
        nt_name = node_tree.name

        self._node_tree_vars[node_tree] = nt_var

        ntp_nt = NTP_ShaderNodeTree(node_tree, nt_var)

        self._initialize_shader_node_tree(ntp_nt, nt_name)

        self._set_node_tree_properties(node_tree)
        
        if bpy.app.version >= (4, 0, 0):
            self._tree_interface_settings(ntp_nt)

        #initialize nodes
        self._write(f"# Initialize {nt_var} nodes\n")
        for node in node_tree.nodes:
            self._process_node(node, ntp_nt)

        for zone_list in ntp_nt.zone_inputs.values():
            self._process_zones(zone_list)

        #set look of nodes
        self._set_parents(node_tree)
        self._set_locations(node_tree)
        self._set_dimensions(node_tree)

        #create connections
        self._init_links(node_tree)
        
        self._write(f"return {nt_var}\n\n")

        #create node group
        self._write(f"{nt_var} = {nt_var}_node_group()\n", self._outer_indent_level)
        

    def execute(self, context):
        if not self._setup_options(context.scene.ntp_options):
            return {'CANCELLED'}
        
        #find node group to replicate
        if self.group_type == 'MATERIAL':
            self.obj = bpy.data.materials[self.name]
        elif self.group_type == 'LIGHT':
            self.obj = bpy.data.lights[self.name]
        elif self.group_type == 'LINE_STYLE':
            self.obj = bpy.data.linestyles[self.name]
        elif self.group_type == 'WORLD':
            self.obj = bpy.data.worlds[self.name]
        
        if self.group_type == 'NODE_GROUP':
            self._base_node_tree = bpy.data.node_groups[self.name]
        else:
            self._base_node_tree = self.obj.node_tree

        if self._base_node_tree is None:
            self.report({'ERROR'}, ("NodeToPython: This doesn't seem to be a "
                                    "valid material. Is Use Nodes selected?"))
            return {'CANCELLED'}

        #set up names to use in generated addon
        self.obj_var = clean_string(self.name)
        
        if self._mode == 'ADDON':
            self._outer_indent_level = 2
            self._inner_indent_level = 3

            if not self._setup_addon_directories(context, self.obj_var):
                return {'CANCELLED'}

            self._file = open(f"{self._addon_dir}/__init__.py", "w")

            self._create_header(self.name)
            self._class_name = clean_string(self.name, lower=False)
            self._init_operator(self.obj_var, self.name)

            self._write("def execute(self, context):", 1)
        else:
            self._file = StringIO("")
            if self._include_imports:
                self._file.write("import bpy\nimport mathutils\n\n\n")

        if self.group_type == 'MATERIAL':
            self._create_material()
        elif self.group_type == 'LIGHT':
            self._create_light()
        elif self.group_type == 'LINE_STYLE':
            self._create_line_style()
        elif self.group_type == 'WORLD':
            self._create_world()
        
        node_trees_to_process = self._topological_sort(self._base_node_tree)

        for node_tree in node_trees_to_process:
            self._process_node_tree(node_tree)

        if self._mode == 'ADDON':
            self._write("return {'FINISHED'}", self._outer_indent_level)
            self._create_menu_func()
            self._create_register_func()
            self._create_unregister_func()
            self._create_main_func()
            self._create_license()
            if bpy.app.version >= (4, 2, 0):
                self._create_manifest()
        else:
            context.window_manager.clipboard = self._file.getvalue()

        self._file.close()
        
        if self._mode == 'ADDON':
            self._zip_addon()

        self._report_finished("material")

        return {'FINISHED'}
    
classes = [
    NTP_OT_Shader
]