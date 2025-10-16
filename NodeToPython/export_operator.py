import bpy

from enum import Enum, auto

class NodeGroupType(Enum):
    COMPOSITOR_NODE_GROUP = auto()
    SCENE = auto()
    GEOMETRY_NODE_GROUP = auto()
    LIGHT = auto()
    LINE_STYLE = auto()
    MATERIAL = auto()
    SHADER_NODE_GROUP = auto()
    WORLD = auto()

class NodeGroupGatherer:
    def __init__(self):
        self.node_groups : dict[NodeGroupType, list] = {
            NodeGroupType.COMPOSITOR_NODE_GROUP : [],
            NodeGroupType.SCENE : [],
            NodeGroupType.GEOMETRY_NODE_GROUP : [],
            NodeGroupType.LIGHT : [],
            NodeGroupType.LINE_STYLE : [],
            NodeGroupType.MATERIAL : [],
            NodeGroupType.SHADER_NODE_GROUP : [],
            NodeGroupType.WORLD : [],
        }

    def gather_node_groups(self, context: bpy.types.Context):
        for group_slot in context.scene.ntp_compositor_node_group_slots:
            if group_slot.node_tree is not None:
                self.node_groups[NodeGroupType.COMPOSITOR_NODE_GROUP].append(
                    group_slot.node_tree
                )
        for scene_slot in context.scene.ntp_scene_slots:
            if scene_slot.scene is not None:
                self.node_groups[NodeGroupType.SCENE].append(scene_slot.scene)

        for group_slot in context.scene.ntp_geometry_node_group_slots:
            if group_slot.node_tree is not None:
                self.node_groups[NodeGroupType.GEOMETRY_NODE_GROUP].append(
                    group_slot.node_tree
                )

        for light_slot in context.scene.ntp_light_slots:
            if light_slot.light is not None:
                self.node_groups[NodeGroupType.LIGHT].append(light_slot.light)

        for line_style_slot in context.scene.ntp_line_style_slots:
            if line_style_slot.line_style is not None:
                self.node_groups[NodeGroupType.LINE_STYLE].append(
                    line_style_slot.line_style
                )

        for material_slot in context.scene.ntp_material_slots:
            if material_slot.material is not None:
                self.node_groups[NodeGroupType.MATERIAL].append(
                    material_slot.material
                )

        for group_slot in context.scene.ntp_shader_node_group_slots:
            if group_slot.node_tree is not None:
                self.node_groups[NodeGroupType.SHADER_NODE_GROUP].append(
                    group_slot.node_tree
                )

        for world_slot in context.scene.ntp_world_slots:
            if world_slot.world is not None:
                self.node_groups[NodeGroupType.WORLD].append(world_slot.world)

    def get_number_node_groups(self) -> int:
        result = 0
        for lst in self.node_groups.values():
            result += len(lst) 
        return result
    
    def get_single_node_group(self):
        # TODO: better name/ergonomics in general
        if self.get_number_node_groups() != 1:
            raise ValueError("Expected just one node group")
        
        for group_type, lst in self.node_groups.items():
            if len(lst) == 1:
                return group_type, lst[0]
            
        raise AssertionError("Expected this to be unreachable")

class NTP_OT_Export(bpy.types.Operator):
    bl_idname = "ntp.export"
    bl_label = "Export"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: bpy.types.Context):
        gatherer = NodeGroupGatherer()
        gatherer.gather_node_groups(context)

        if gatherer.get_number_node_groups() != 1:
            self.report({'ERROR'}, "Can only export one node group currently")
            return {'CANCELLED'}
        
        group_type, obj = gatherer.get_single_node_group()

        if group_type == NodeGroupType.COMPOSITOR_NODE_GROUP:
            bpy.ops.ntp.compositor(compositor_name=obj.name, is_scene=False)
        elif group_type == NodeGroupType.SCENE:
            bpy.ops.ntp.compositor(compositor_name=obj.name, is_scene=True)
        elif group_type == NodeGroupType.GEOMETRY_NODE_GROUP:
            bpy.ops.ntp.geometry_nodes(geo_nodes_group_name=obj.name)
        elif group_type == NodeGroupType.LIGHT:
            bpy.ops.ntp.shader(name=obj.name, group_type='LIGHT')
        elif group_type == NodeGroupType.LINE_STYLE:
            bpy.ops.ntp.shader(name=obj.name, group_type='LINE_STYLE')
        elif group_type == NodeGroupType.MATERIAL:
            bpy.ops.ntp.shader(name=obj.name, group_type='MATERIAL')
        elif group_type == NodeGroupType.SHADER_NODE_GROUP:
            bpy.ops.ntp.shader(name=obj.name, group_type='NODE_GROUP')
        elif group_type == NodeGroupType.WORLD:
            bpy.ops.ntp.shader(name=obj.name, group_type='WORLD')

        return {'FINISHED'}
    
classes = [
    NTP_OT_Export
]