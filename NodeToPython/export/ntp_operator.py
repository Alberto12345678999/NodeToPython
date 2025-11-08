import datetime
from io import StringIO
import os
import pathlib
import shutil
from typing import TextIO, Callable

import bpy

from .node_group_gatherer import NodeGroupGatherer, NodeGroupType
from .license_templates import license_templates
from .ntp_options import NTP_PG_Options
from .utils import *

INDEX = "i"
IMAGE_DIR_NAME = "imgs"
IMAGE_PATH = "image_path"
ITEM = "item"
BASE_DIR = "base_dir"
DATAFILES_PATH = "datafiles_path"
LIB_RELPATH = "lib_relpath"
LIB_PATH = "lib_path"
DATA_SRC = "data_src"
DATA_DST = "data_dst"

RESERVED_NAMES = {
    INDEX,
    IMAGE_DIR_NAME,
    IMAGE_PATH,
    ITEM,
    BASE_DIR,
    DATAFILES_PATH,
    LIB_RELPATH,
    LIB_PATH,
    DATA_SRC,
    DATA_DST
}

#node input sockets that are messy to set default values for
DONT_SET_DEFAULTS = {
    'NodeSocketGeometry',
    'NodeSocketShader',
    'NodeSocketMatrix',
    'NodeSocketVirtual',
    'NodeSocketBundle',
    'NodeSocketClosure'
}

MAX_BLENDER_VERSION = (5, 1, 0)

class NTP_OT_Export(bpy.types.Operator):
    bl_idname = "ntp.export"
    bl_label = "Export"
    bl_description = "Export node group(s) to Python"
    bl_options = {'REGISTER', 'UNDO'}

    # node tree input sockets that have default properties
    if bpy.app.version < (4, 0, 0):
        default_sockets_v3 = {'VALUE', 'INT', 'BOOLEAN', 'VECTOR', 'RGBA'}
    else:
        nondefault_sockets_v4 = {
            bpy.types.NodeTreeInterfaceSocketCollection,
            bpy.types.NodeTreeInterfaceSocketGeometry,
            bpy.types.NodeTreeInterfaceSocketImage,
            bpy.types.NodeTreeInterfaceSocketMaterial,
            bpy.types.NodeTreeInterfaceSocketObject,
            bpy.types.NodeTreeInterfaceSocketShader,
            bpy.types.NodeTreeInterfaceSocketTexture,
            bpy.types.NodeTreeInterfaceSocketClosure
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Write functions after nodes are mostly initialized and linked up
        self._write_after_links: list[Callable] = []

        # File (TextIO) or string (StringIO) the add-on/script is generated into
        self._file: TextIO | StringIO = StringIO()

        # Path to the directory of the zip file
        self._zip_dir: str = ""

        # Path to the directory for the generated addon
        self._addon_dir: str = ""

        # Class named for the generated operator
        self._class_name: str = ""

        # Indentation to use for the default write function
        self._outer_indent_level: int = 0
        self._inner_indent_level: int = 1

        # Dictionary to keep track of variables->usage count pairs
        self._used_vars: dict[str, int] = {}

        for name in RESERVED_NAMES:
            self._used_vars[name] = 0

        # Generate socket default, min, and max values
        self._include_group_socket_values = True

        # Set dimensions of generated nodes
        self._should_set_dimensions = True

        # Indentation string (default: four spaces)
        self._indentation = "    "

        self._link_external_node_groups = True

        self._lib_trees: dict[pathlib.Path, list[bpy.types.NodeTree]] = {}

        if bpy.app.version >= (3, 4, 0):
            # Set default values for hidden sockets
            self._set_unavailable_defaults = False

    def execute(self, context: bpy.types.Context):
        if bpy.app.version >= MAX_BLENDER_VERSION:
            self.report(
                {'WARNING'},
                f"Blender version {bpy.app.version} is not supported yet!\n"
                f"NodeToPython is currently supported up to "
                f"{vec3_to_py_str(MAX_BLENDER_VERSION)}.\n"
                f"Some nodes, settings, and features may not work yet. "
                f" For more details, visit "
            )
            self.report(
                {'WARNING'},
                "\t\thttps://github.com/BrendanParmer/NodeToPython/blob/main/"
                "docs/README.md#supported-versions "
            )
            return {'CANCELLED'}
        
        if not self._setup_options(getattr(context.scene, "ntp_options")):
            return {'CANCELLED'}
        
        if self._mode == 'ADDON':
            self._outer_indent_level = 2
            self._inner_indent_level = 3

            if not self._setup_addon_directories(self.name):
                return {'CANCELLED'}
            
            self._file = open(f"{self._addon_dir}/__init__.py", "w")

            self._create_bl_info(self.name)
            self._create_imports()

            #self._init_operator(self.obj_var, self.name)
            #self._write("def execute(self, context):", 1)

        elif self._mode == 'SCRIPT':
            self._file = StringIO("")
            if self._include_imports:
                self._create_imports()

        gatherer = NodeGroupGatherer()
        gatherer.gather_node_groups(context)

        # TODO: multiple node groups
        if gatherer.get_number_node_groups() != 1:
            self.report({'ERROR'}, "Can only export one node group currently")
            return {'CANCELLED'}
        
        group_type, obj = gatherer.get_single_node_group()

        # Imported here to avoid circular dependency issues
        from .compositor.exporter import CompositorExporter
        from .geometry.exporter import GeometryNodesExporter
        from .shader.exporter import ShaderExporter

        match group_type:
            case NodeGroupType.COMPOSITOR_NODE_GROUP | NodeGroupType.SCENE:
                exporter = CompositorExporter(self, obj.name, group_type)
            case NodeGroupType.GEOMETRY_NODE_GROUP:
                exporter = GeometryNodesExporter(self, obj.name, group_type)
            case (  NodeGroupType.LIGHT 
                  | NodeGroupType.LINE_STYLE
                  | NodeGroupType.MATERIAL
                  | NodeGroupType.SHADER_NODE_GROUP
                  | NodeGroupType.WORLD
            ):
                exporter = ShaderExporter(self, obj.name, group_type)
        exporter.export()

        if self._mode == 'ADDON':
            self._write("return {'FINISHED'}\n", self._outer_indent_level)

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

        return {'FINISHED'}
    
    def _write(self, string: str, indent_level: int = -1):
        if indent_level == -1:
            indent_level = self._inner_indent_level
        indent_str = indent_level * self._indentation
        self._file.write(f"{indent_str}{string}\n")

    def _setup_options(self, options: NTP_PG_Options) -> bool:
        # General
        self._mode = options.mode
        self._include_group_socket_values = options.set_group_defaults
        self._should_set_dimensions = options.set_node_sizes

        if options.indentation_type == 'SPACES_2':
            self._indentation = "  "
        elif options.indentation_type == 'SPACES_4':
            self._indentation = "    "
        elif options.indentation_type == 'SPACES_8':
            self._indentation = "        "
        elif options.indentation_type == 'TABS':
            self._indentation = "\t"

        self._link_external_node_groups = options.link_external_node_groups

        if bpy.app.version >= (3, 4, 0):
            self._set_unavailable_defaults = options.set_unavailable_defaults

        #Script
        if options.mode == 'SCRIPT':
            self._include_imports = options.include_imports
        #Addon
        elif options.mode == 'ADDON':
            self._dir_path = bpy.path.abspath(options.dir_path)
            self._name_override = options.name_override
            self._description = options.description
            self._author_name = options.author_name
            self._version = options.version
            self._location = options.location
            self._license = options.license
            self._should_create_license = options.should_create_license
            self._category = options.category
            self._custom_category = options.custom_category
            if options.menu_id in dir(bpy.types):
                self._menu_id = options.menu_id
            else:
                self.report({'ERROR'}, f"{options.menu_id} is not a valid menu")
                return False
        return True

    def _setup_addon_directories(
        self,
        addon_name: str
    ) -> bool:
        """
        Finds/creates directories to save add-on to

        Parameters:
        context (Context): the current scene context
        obj_var (str): variable name of the object

        Returns:
        (bool): success of addon directory setup
        """
        if not self._dir_path or self._dir_path == "":
            self.report({'ERROR'},
                        ("NodeToPython: No save location found. Please select "
                         "one in the NodeToPython Options panel"))
            return False

        self._zip_dir = os.path.join(self._dir_path, addon_name)
        self._addon_dir = os.path.join(self._zip_dir, addon_name)

        if not os.path.exists(self._addon_dir):
            os.makedirs(self._addon_dir)
        
        return True

    def _create_bl_info(self, name: str) -> None:
        """
        Sets up the bl_info and imports the Blender API

        Parameters:
        name (str): name of the add-on
        """

        self._write("bl_info = {", 0)
        self._name = name
        if self._name_override and self._name_override != "":
            self._name = self._name_override
        self._write(f"\"name\" : {str_to_py_str(self._name)},", 1)
        if self._description and self._description != "":
            self._write(f"\"description\" : {str_to_py_str(self._description)},", 1)
        self._write(f"\"author\" : {str_to_py_str(self._author_name)},", 1)
        self._write(f"\"version\" : {vec3_to_py_str(self._version)},", 1)
        self._write(f"\"blender\" : {bpy.app.version},", 1)
        self._write(f"\"location\" : {str_to_py_str(self._location)},", 1)
        category = self._category
        if category == "Custom":
            category = self._custom_category
        self._write(f"\"category\" : {str_to_py_str(category)},", 1)
        self._write("}\n", 0)

    def _create_imports(self) -> None:
        self._write("import bpy", 0)
        self._write("import mathutils", 0)
        self._write("import os", 0)
        self._write("\n", 0)

    def _create_menu_func(self) -> None:
        """
        Creates the menu function
        """
        self._write("def menu_func(self, context):", 0)
        self._write(f"self.layout.operator({self._class_name}.bl_idname)\n", 1)

    def _create_register_func(self) -> None:
        """
        Creates the register function
        """
        self._write("def register():", 0)
        self._write(f"bpy.utils.register_class({self._class_name})", 1)
        self._write(f"bpy.types.{self._menu_id}.append(menu_func)\n", 1)

    def _create_unregister_func(self) -> None:
        """
        Creates the unregister function
        """
        self._write("def unregister():", 0)
        self._write(f"bpy.utils.unregister_class({self._class_name})", 1)
        self._write(f"bpy.types.{self._menu_id}.remove(menu_func)\n", 1)

    def _create_main_func(self) -> None:
        """
        Creates the main function
        """
        self._write("if __name__ == \"__main__\":", 0)
        self._write("register()", 1)

    def _create_license(self) -> None:
        if not self._should_create_license:
            return
        if self._license == 'OTHER':
            return
        license_file = open(f"{self._addon_dir}/LICENSE", "w")
        year = datetime.date.today().year
        license_txt = license_templates[self._license](year, self._author_name)
        license_file.write(license_txt)
        license_file.close()

    if bpy.app.version >= (4, 2, 0):
        def _create_manifest(self) -> None:
            manifest = open(f"{self._addon_dir}/blender_manifest.toml", "w")
            manifest.write("schema_version = \"1.0.0\"\n\n")
            idname = self._name_override.lower() #TODO: this isn't safe
            manifest.write(f"id = {str_to_py_str(idname)}\n")

            manifest.write(f"version = {version_to_manifest_str(self._version)}\n")
            manifest.write(f"name = {str_to_py_str(self._name)}\n")
            if self._description == "":
                self._description = self._name
            manifest.write(f"tagline = {str_to_py_str(self._description)}\n")
            manifest.write(f"maintainer = {str_to_py_str(self._author_name)}\n")
            manifest.write("type = \"add-on\"\n")
            min_version_str = f"{version_to_manifest_str(bpy.app.version)}"
            manifest.write(f"blender_version_min = {min_version_str}\n")
            if self._license != 'OTHER':
                manifest.write(f"license = [{str_to_py_str(self._license)}]\n")
            else:
                self.report(
                    {'WARNING'}, 
                    "No license selected. Please add a license to "
                    "the manifest file"
                )

            manifest.close()

    def _zip_addon(self) -> None:
        """
        Zips up the addon and removes the directory
        """
        shutil.make_archive(self._zip_dir, "zip", self._zip_dir)
        shutil.rmtree(self._zip_dir)

    def _report_finished(self, object: str):
        """
        Alert user that NTP is finished

        Parameters:
        object (str): the copied node tree or encapsulating structure
            (geometry node modifier, material, scene, etc.)
        """
        if self._mode == 'SCRIPT':
            location = "clipboard"
        else:
            location = self._dir_path
        self.report({'INFO'}, f"NodeToPython: Saved {object} to {location}")

classes = [
    NTP_OT_Export
]