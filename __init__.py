import bpy
from bpy.props import IntProperty, BoolProperty, StringProperty
from bpy.app.handlers import persistent
import time
import os
import tempfile

bl_info = {
    "name": "Custom Autosave",
    "author": "SlaneDRV",
    "version": (1, 6),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Custom Autosave",
    "description": "Customizable autosave functionality with option for unsaved files",
    "category": "System",
}

class AutosaveSettings(bpy.types.PropertyGroup):
    enabled: BoolProperty(
        name="Enable Autosave",
        description="Enable or disable autosave",
        default=True
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
                print(f"Unsaved file automatically saved to {full_path}")
            else:
                print("File not saved. Autosave skipped.")
                return settings.interval
        else:
            print(f"Autosave triggered at {time.strftime('%H:%M:%S')}")
            bpy.ops.wm.save_mainfile()
            print(f"File saved at {time.strftime('%H:%M:%S')}")
    else:
        print("Autosave is disabled or settings are not available")
    
    return settings.interval if settings else 60

def init_autosave_timer():
    if bpy.app.timers.is_registered(auto_save):
        bpy.app.timers.unregister(auto_save)
    
    settings = get_autosave_settings()
    interval = settings.interval if settings else 60
    bpy.app.timers.register(auto_save, first_interval=interval)
    print(f"Autosave timer initialized with interval {interval} seconds")

class AutosavePanel(bpy.types.Panel):
    bl_label = "Custom Autosave"
    bl_idname = "OBJECT_PT_custom_autosave"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Custom Autosave'

    @classmethod
    def poll(cls, context):
        return context.scene is not None

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
        self.report({'INFO'}, f"Autosave timer restarted with interval {context.scene.autosave_settings.interval} seconds")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(AutosaveSettings)
    bpy.utils.register_class(AutosavePanel)
    bpy.utils.register_class(WM_OT_RestartAutosaveTimer)
    bpy.types.Scene.autosave_settings = bpy.props.PointerProperty(type=AutosaveSettings)
    bpy.app.timers.register(init_autosave_timer, first_interval=1.0)

def unregister():
    if bpy.app.timers.is_registered(auto_save):
        bpy.app.timers.unregister(auto_save)
    bpy.utils.unregister_class(WM_OT_RestartAutosaveTimer)
    bpy.utils.unregister_class(AutosavePanel)
    bpy.utils.unregister_class(AutosaveSettings)
    del bpy.types.Scene.autosave_settings

if __name__ == "__main__":
    register()