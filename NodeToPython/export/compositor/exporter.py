import bpy

from ..node_group_gatherer import NodeGroupType
from ..node_settings import NTPNodeSetting, ST
from ..node_tree_exporter import NodeTreeExporter, INDEX, NODE_TREE_NAMES
from ..ntp_node_tree import NTP_NodeTree
from ..ntp_operator import NTP_OT_Export, NodeTreeInfo
from ..utils import *

SCENE = "scene"
BASE_NAME = "base_name"
END_NAME = "end_name"
NODE = "node"

COMP_OP_RESERVED_NAMES = {SCENE, BASE_NAME, END_NAME, NODE} 

class CompositorExporter(NodeTreeExporter):
    def __init__(
        self,
        ntp_operator: NTP_OT_Export,
        node_tree_info: NodeTreeInfo
    ):
        if not node_tree_info._group_type.is_compositor():
            ntp_operator.report(
                {'ERROR'},
                f"Cannot initialize CompositorExporter with group type "
                f"{node_tree_info._group_type}"
            )
        NodeTreeExporter.__init__(self, ntp_operator, node_tree_info)
        for name in COMP_OP_RESERVED_NAMES:
            self._used_vars[name] = 0
    
    def _create_scene(self):
        indent_level = self._get_obj_creation_indent()

        #TODO: wrap in more general unique name util function
        self._write(f"# Generate unique scene name", indent_level)
        self._write(f"{BASE_NAME} = {str_to_py_str(self._node_tree_info._obj.name)}",
                    indent_level)
        self._write(f"{END_NAME} = {BASE_NAME}", indent_level)
        self._write(f"if bpy.data.scenes.get({END_NAME}) is not None:", indent_level)

        self._write(f"{INDEX} = 1", indent_level + 1)
        self._write(f"{END_NAME} = {BASE_NAME} + f\".{{i:03d}}\"", 
                    indent_level + 1)
        self._write(f"while bpy.data.scenes.get({END_NAME}) is not None:",
                    indent_level + 1)
        
        self._write(f"{END_NAME} = {BASE_NAME} + f\".{{{INDEX}:03d}}\"", 
                    indent_level + 2)
        self._write(f"{INDEX} += 1\n", indent_level + 2)

        self._write(f"bpy.ops.scene.new(type='NEW')", indent_level)
        self._write(f"{SCENE} = bpy.context.scene", indent_level)
        self._write(f"{SCENE}.name = {END_NAME}", indent_level)
        self._write(f"{SCENE}.use_fake_user = True", indent_level)
        self._write(f"bpy.context.window.scene = {SCENE}", indent_level)
        self._write("", 0)

    # NodeTreeExporter interface
    def _create_obj(self):
        if self._node_tree_info._group_type == NodeGroupType.SCENE:
            self._create_scene()

    # NodeTreeExporter interface
    def _initialize_node_tree(
        self, 
        ntp_node_tree: NTP_NodeTree
    ) -> None:
        nt_name = ntp_node_tree._node_tree.name

        self._node_tree_info._func = f"{ntp_node_tree._var}_node_group"
        #initialize node group
        self._write(f"def {self._node_tree_info._func}("
                    f"{NODE_TREE_NAMES}: dict[typing.Callable, str]):", 
                    self._operator._outer_indent_level)
        self._write(f'"""Initialize {nt_name} node group"""')

        is_tree_base = (ntp_node_tree._node_tree == self._base_node_tree)
        is_scene = self._node_tree_info._group_type == NodeGroupType.SCENE
        if is_tree_base and is_scene:
            self._write("if bpy.app.version < (5, 0, 0):")
            self._write(f"{ntp_node_tree._var} = {SCENE}.node_tree",
                        self._operator._inner_indent_level + 1)
            self._write("else:")
            self._write((f"{SCENE}.compositing_node_group = "
                         f"bpy.data.node_groups.new("
                         f"type = \'CompositorNodeTree\', "
                         f"name = {str_to_py_str(nt_name)})"),
                         self._operator._inner_indent_level + 1)
            self._write(f"{ntp_node_tree._var} = {SCENE}.compositing_node_group",
                        self._operator._inner_indent_level + 1)
            self._write("", 0)
            self._write(f"# Start with a clean node tree")
            self._write(f"for {NODE} in {ntp_node_tree._var}.nodes:")
            self._write(f"{ntp_node_tree._var}.nodes.remove({NODE})", 
                        self._operator._inner_indent_level + 1)
        else:
            self._write((f"{ntp_node_tree._var} = bpy.data.node_groups.new("
                         f"type = \'CompositorNodeTree\', "
                         f"name = {str_to_py_str(nt_name)})"))
            self._write("", 0)

        # Compositor node tree settings
        #TODO: might be good to make this optional
        enum_settings = ["chunk_size", "edit_quality", "execution_mode",
                         "precision", "render_quality"]
        for enum in enum_settings:
            if not hasattr(ntp_node_tree._node_tree, enum):
                continue
            setting = getattr(ntp_node_tree._node_tree, enum)
            if setting != None and setting != "":
                py_str = enum_to_py_str(setting)
                self._write(f"{ntp_node_tree._var}.{enum} = {py_str}")
        
        bool_settings = ["use_groupnode_buffer", "use_opencl", "use_two_pass",
                         "use_viewer_border"]
        for bool_setting in bool_settings:
            if not hasattr(ntp_node_tree._node_tree, bool_setting):
                continue
            if getattr(ntp_node_tree._node_tree, bool_setting) is True:
                self._write(f"{ntp_node_tree._var}.{bool_setting} = True")

    def _process_node(self, node: bpy.types.Node, ntp_nt: NTP_NodeTree) -> None:
        if bpy.app.version < (4, 5, 0):
            if node.bl_idname == 'CompositorNodeColorBalance':
                self._set_color_balance_settings(node)
        NodeTreeExporter._process_node(self, node, ntp_nt)

    if bpy.app.version < (4, 5, 0):
        def _set_color_balance_settings(
            self, 
            node: bpy.types.CompositorNodeColorBalance
        ) -> None:
            """
            Sets the color balance settings so we only set the active variables,
            preventing conflict

            node (CompositorNodeColorBalance): the color balance node
            """
            correction_method = getattr(node, "correction_method")
            if correction_method == 'LIFT_GAMMA_GAIN':
                lst = [
                    NTPNodeSetting("correction_method", ST.ENUM),                 
                    NTPNodeSetting("gain",  ST.VEC3,  max_version_=(3, 5, 0)),
                    NTPNodeSetting("gain",  ST.COLOR, min_version_=(3, 5, 0), max_version_=(4, 5, 0)),
                    NTPNodeSetting("gamma", ST.VEC3,  max_version_=(3, 5, 0)),
                    NTPNodeSetting("gamma", ST.COLOR, min_version_=(3, 5, 0), max_version_=(4, 5, 0)),
                    NTPNodeSetting("lift",  ST.VEC3,  max_version_=(3, 5, 0)),
                    NTPNodeSetting("lift",  ST.COLOR, min_version_=(3, 5, 0), max_version_=(4, 5, 0))
                ]
            elif correction_method == 'OFFSET_POWER_SLOPE':
                lst = [
                    NTPNodeSetting("correction_method", ST.ENUM),
                    NTPNodeSetting("offset", ST.VEC3,  max_version_=(3, 5, 0)),
                    NTPNodeSetting("offset", ST.COLOR, min_version_=(3, 5, 0), max_version_=(4, 5, 0)),
                    NTPNodeSetting("offset_basis", ST.FLOAT),
                    NTPNodeSetting("power", ST.VEC3,  max_version_=(3, 5, 0)),
                    NTPNodeSetting("power", ST.COLOR, min_version_=(3, 5, 0), max_version_=(4, 5, 0)),
                    NTPNodeSetting("slope", ST.VEC3,  max_version_=(3, 5, 0)),
                    NTPNodeSetting("slope", ST.COLOR, min_version_=(3, 5, 0), max_version_=(4, 5, 0))
                ]
            elif correction_method == 'WHITEPOINT':
                lst = [
                    NTPNodeSetting("correction_method", ST.ENUM, max_version_=(4, 5, 0)),
                    NTPNodeSetting("input_temperature", ST.FLOAT, max_version_=(4, 5, 0)),
                    NTPNodeSetting("input_tint", ST.FLOAT, max_version_=(4, 5, 0)),
                    NTPNodeSetting("output_temperature", ST.FLOAT, max_version_=(4, 5, 0)),
                    NTPNodeSetting("output_tint", ST.FLOAT, max_version_=(4, 5, 0))
                ]
            else:
                self._operator.report({'ERROR'},
                            f"Unknown color balance correction method "
                            f"{enum_to_py_str(correction_method)}")
                return

            color_balance_info = self._node_settings['CompositorNodeColorBalance']
            self._node_settings['CompositorNodeColorBalance'] = color_balance_info._replace(attributes_ = lst)