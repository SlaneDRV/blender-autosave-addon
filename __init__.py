import bpy
from bpy.props import IntProperty, BoolProperty, StringProperty, EnumProperty
from bpy.app.handlers import persistent
import time
import os
import tempfile

bl_info = {
    "name": "Custom Autosave",
    "author": "SlaneDRV",
    "version": (1, 7),
    "blender": (2, 80, 0),
    "location": "Properties > Output > Custom Autosave",
    "description": "Customizable autosave functionality with option for unsaved files",
    "category": "System",
}

class AutosaveSettings(bpy.types.PropertyGroup):
    enabled: BoolProperty(
        name="Enable Autosave",
        description="Enable or disable autosave",
        default=False
    )
    interval: IntProperty(
        name="Autosave Interval",
        description="Interval between autosaves in seconds",
        default=60,
        min=10,
        max=3600
    )
    save_unsaved: BoolProperty(
        name="Save Unsaved Files",
        description="Automatically save unsaved files to temp folder",
        default=False
    )
    temp_path: StringProperty(
        name="Temp Save Path",
        description="Path for temporary saves of unsaved files",
        default=tempfile.gettempdir(),
        subtype='DIR_PATH'
    )

class AutosaveAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    panel_location: EnumProperty(
        name="Panel Location",
        items=[
            ('OUTPUT', "Output Properties", "Show in Output Properties"),
            ('VIEW3D', "3D Viewport", "Show in 3D Viewport sidebar"),
        ],
        default='OUTPUT',
        description="Choose where to display the Custom Autosave panel"
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "panel_location")

def get_autosave_settings():
    if hasattr(bpy.context, 'scene') and hasattr(bpy.context.scene, 'autosave_settings'):
        return bpy.context.scene.autosave_settings
    return None

def is_file_saved():
    return bpy.data.is_saved and not bpy.data.is_dirty

def auto_save():
    settings = get_autosave_settings()
    if settings and settings.enabled:
        if not is_file_saved():
            if settings.save_unsaved:
                temp_path = settings.temp_path
                file_name = "unsaved_blender_file.blend"
                full_path = os.path.join(temp_path, file_name)
                
                bpy.ops.wm.save_as_mainfile(filepath=full_path)
        else:
            bpy.ops.wm.save_mainfile()
    
    return settings.interval if settings and settings.enabled else None

def init_autosave_timer():
    if bpy.app.timers.is_registered(auto_save):
        bpy.app.timers.unregister(auto_save)
    
    settings = get_autosave_settings()
    if settings and settings.enabled:
        interval = settings.interval
        bpy.app.timers.register(auto_save, first_interval=interval)

class AutosavePanel(bpy.types.Panel):
    bl_label = "Custom Autosave"
    bl_idname = "OBJECT_PT_custom_autosave"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "output"

    @classmethod
    def poll(cls, context):
        preferences = context.preferences.addons[__name__].preferences
        return (preferences.panel_location == 'OUTPUT' and
                context.scene is not None)

    def draw(self, context):
        layout = self.layout
        settings = context.scene.autosave_settings

        layout.prop(settings, "enabled")
        layout.prop(settings, "interval")
        layout.prop(settings, "save_unsaved")
        
        if settings.save_unsaved:
            layout.prop(settings, "temp_path")
        
        layout.operator("wm.restart_autosave_timer")

class AutosavePanelViewport(bpy.types.Panel):
    bl_label = "Custom Autosave"
    bl_idname = "VIEW3D_PT_custom_autosave"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Custom Autosave'

    @classmethod
    def poll(cls, context):
        preferences = context.preferences.addons[__name__].preferences
        return (preferences.panel_location == 'VIEW3D' and
                context.scene is not None)

    def draw(self, context):
        layout = self.layout
        settings = context.scene.autosave_settings

        layout.prop(settings, "enabled")
        layout.prop(settings, "interval")
        layout.prop(settings, "save_unsaved")
        
        if settings.save_unsaved:
            layout.prop(settings, "temp_path")
        
        layout.operator("wm.restart_autosave_timer")

class WM_OT_RestartAutosaveTimer(bpy.types.Operator):
    bl_idname = "wm.restart_autosave_timer"
    bl_label = "Restart Autosave Timer"

    def execute(self, context):
        init_autosave_timer()
        self.report({'INFO'}, f"Autosave timer {'started' if context.scene.autosave_settings.enabled else 'stopped'}")
        return {'FINISHED'}

classes = (
    AutosaveSettings,
    AutosaveAddonPreferences,
    AutosavePanel,
    AutosavePanelViewport,
    WM_OT_RestartAutosaveTimer,
)

@persistent
def reset_autosave_settings(dummy):
    settings = get_autosave_settings()
    if settings:
        settings.enabled = False
        settings.save_unsaved = False

def register_handlers():
    bpy.app.handlers.load_post.append(reset_autosave_settings)

def unregister_handlers():
    bpy.app.handlers.load_post.remove(reset_autosave_settings)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.autosave_settings = bpy.props.PointerProperty(type=AutosaveSettings)
    bpy.app.timers.register(init_autosave_timer, first_interval=1.0)
    register_handlers()

def unregister():
    if bpy.app.timers.is_registered(auto_save):
        bpy.app.timers.unregister(auto_save)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.autosave_settings
    unregister_handlers()

if __name__ == "__main__":
    register()