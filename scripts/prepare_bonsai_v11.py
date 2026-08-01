import os
from pathlib import Path
import math
import bpy
from mathutils import Vector

repo_root = Path(__file__).resolve().parents[1]
project = Path(os.environ.get("KIN_HOUSE_OUTPUT", repo_root / "generated"))
ifc_path = project / "kin-house.ifc"
blend_path = project / "kin-house-bonsai.blend"
qa_path = project / "renders" / "bonsai-model-qa.jpg"
qa_path.parent.mkdir(parents=True, exist_ok=True)

result = bpy.ops.bim.load_project(filepath=str(ifc_path), should_start_fresh_session=True)
if result != {"FINISHED"}:
    raise RuntimeError(f"Bonsai IFC import failed: {result}")

for obj in list(bpy.data.objects):
    if obj.type in {"CAMERA", "LIGHT"}:
        bpy.data.objects.remove(obj, do_unlink=True)

camera_data = bpy.data.cameras.new("Bonsai QA Camera")
camera = bpy.data.objects.new("Bonsai QA Camera", camera_data)
bpy.context.scene.collection.objects.link(camera)
camera.location = (20.5, -25.0, 14.8)
camera.rotation_euler = (Vector((7.4, 4.0, 4.3)) - camera.location).to_track_quat("-Z", "Y").to_euler()
camera_data.lens = 56
bpy.context.scene.camera = camera

sun_data = bpy.data.lights.new("Bonsai QA Sun", "SUN")
sun_data.energy = 3.2
sun_data.angle = math.radians(18)
sun = bpy.data.objects.new("Bonsai QA Sun", sun_data)
bpy.context.scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(28), math.radians(-18), math.radians(-32))

area_data = bpy.data.lights.new("Bonsai QA Area", "AREA")
area_data.energy = 1350
area_data.size = 11
area = bpy.data.objects.new("Bonsai QA Area", area_data)
bpy.context.scene.collection.objects.link(area)
area.location = (7.4, -9.0, 12.0)
area.rotation_euler = (Vector((7.4, 3.0, 3.7)) - area.location).to_track_quat("-Z", "Y").to_euler()

world = bpy.context.scene.world or bpy.data.worlds.new("Bonsai QA World")
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.065, 0.080, 0.085, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.48

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 1120
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "JPEG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.quality = 90
scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.filepath = str(qa_path)
bpy.ops.render.render(write_still=True)

# Open the saved project in a readable coloured camera view instead of the grey solid overview.
for screen in bpy.data.screens:
    for area_view in screen.areas:
        if area_view.type == "VIEW_3D":
            area_view.spaces.active.shading.type = "MATERIAL"
            area_view.spaces.active.region_3d.view_perspective = "CAMERA"

scene["ProjectStage"] = "Concept BIM / LOD 200 — NOT FOR CONSTRUCTION"
scene["EnvelopeRevision"] = "1.2 — coordinated roof edges, pavilion joints and facade openings"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)

print("BONSAI_IMPORT", result)
print("BONSAI_OBJECTS", len(bpy.data.objects))
print("BONSAI_MATERIALS", len(bpy.data.materials))
print("BONSAI_QA_RENDER", qa_path)
