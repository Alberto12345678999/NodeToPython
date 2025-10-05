import bpy

class NTP_MT_NodeToPython(bpy.types.Menu):
    bl_idname = "NTP_MT_node_to_python"
    bl_label = "Node To Python"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout.column_flow(columns=1)
        layout.operator_context = 'INVOKE_DEFAULT'

classes = [
    NTP_MT_NodeToPython
]