from __future__ import annotations

import math
import os
from pathlib import Path

import bpy
import numpy as np
import ifcopenshell
from ifcopenshell.api import aggregate, context, feature, geometry, material, project, pset, root, spatial, style, unit


REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get("KIN_HOUSE_OUTPUT", REPO_ROOT / "generated"))
OUT.mkdir(parents=True, exist_ok=True)

PROJECT_NAME = "KIN House — Mountain Courtyard Residence"
GROUND_Z = 0.0
UPPER_Z = 3.25
GROUND_H = 3.05
UPPER_H = 3.20

ROOMS_GROUND = [
    ("G01", "Гостиная", 28.6, (0.30, 0.30, 7.15, 4.00)),
    ("G02", "Кухня-столовая", 23.4, (7.35, 0.30, 5.85, 4.00)),
    ("G03", "Кладовая кухни", 3.2, (13.40, 0.30, 0.80, 4.00)),
    ("G04", "Двухсветный холл", 13.8, (0.30, 4.45, 4.3125, 3.20)),
    ("G05", "Кабинет / гостевая", 12.6, (4.8125, 4.45, 3.9375, 3.20)),
    ("G06", "Гибкая комната", 10.4, (8.95, 4.45, 3.25, 3.20)),
    ("G07", "Гостевой душ", 4.1, (12.40, 4.45, 1.28125, 3.20)),
    ("G08", "Лестница и коридор", 9.6, (0.30, 7.80, 4.363636, 2.20)),
    ("G09", "Постирочная", 6.4, (4.813636, 7.80, 2.909091, 2.20)),
    ("G10", "Гардероб входа", 2.8, (7.872727, 7.80, 1.272727, 2.20)),
    ("G11", "Техническая", 5.2, (9.295455, 7.80, 2.363636, 2.20)),
    ("G12", "Хранение", 5.9, (11.809091, 7.80, 2.681818, 2.20)),
]

ROOMS_UPPER = [
    ("U01", "Главная спальня", 17.2, (0.30, 0.30, 3.822222, 4.50)),
    ("U02", "Спальня 2", 13.6, (4.272222, 0.30, 3.022222, 4.50)),
    ("U03", "Спальня 3", 13.1, (7.444444, 0.30, 2.911111, 4.50)),
    ("U04", "Гардероб главной спальни", 5.4, (0.30, 5.00, 2.454545, 2.20)),
    ("U05", "Ванная главной спальни", 6.0, (2.904545, 5.00, 2.727273, 2.20)),
    ("U06", "Общая ванная", 6.7, (10.00, 5.00, 3.045455, 2.20)),
    ("U07", "Бельевой шкаф", 2.1, (13.195455, 5.00, 0.954545, 2.20)),
    ("U08", "Галерея / лестница", 12.4, (5.50, 7.40, 4.133333, 3.00)),
    ("U09", "Семейная гостиная", 12.5, (9.983333, 7.40, 4.166667, 3.00)),
]

VOLUMES = [
    dict(name="Left Concrete Gable", x=0.0, y=0.0, w=5.15, d=10.20, eave=6.45, ridge=8.75, finish="concrete"),
    dict(name="Central Charred Timber Gable", x=5.00, y=0.0, w=5.05, d=10.80, eave=6.70, ridge=9.80, finish="timber"),
    dict(name="Right Rear Timber Gable", x=10.00, y=4.00, w=4.80, d=6.40, eave=6.15, ridge=8.45, finish="timber"),
]


def matrix(x=0.0, y=0.0, z=0.0, angle=0.0):
    c, s = math.cos(angle), math.sin(angle)
    return np.array(((c, -s, 0, x), (s, c, 0, y), (0, 0, 1, z), (0, 0, 0, 1)), dtype=float)


def ifc_pset(model, product, name, properties):
    prop = pset.add_pset(model, product=product, name=name)
    pset.edit_pset(model, pset=prop, properties=properties)


def build_ifc(path: Path):
    model = project.create_file(version="IFC4")
    model.header.file_name.name = path.name
    model.header.file_name.author = ("Codex BIM House Architect",)
    model.header.file_name.organization = ("KIN House concept project",)
    model.header.file_description.description = ("ViewDefinition [DesignTransferView]",)
    proj = root.create_entity(model, ifc_class="IfcProject", name=PROJECT_NAME)
    unit.assign_unit(model)
    model_ctx = context.add_context(model, context_type="Model")
    body = context.add_context(model, context_type="Model", context_identifier="Body", target_view="MODEL_VIEW", parent=model_ctx)

    site = root.create_entity(model, ifc_class="IfcSite", name="Условный участок — требуется привязка")
    building = root.create_entity(model, ifc_class="IfcBuilding", name="KIN House")
    ground = root.create_entity(model, ifc_class="IfcBuildingStorey", name="01 Первый этаж")
    ground.Elevation = GROUND_Z
    upper = root.create_entity(model, ifc_class="IfcBuildingStorey", name="02 Второй этаж")
    upper.Elevation = UPPER_Z
    roof_level = root.create_entity(model, ifc_class="IfcBuildingStorey", name="03 Кровля")
    roof_level.Elevation = 6.45
    aggregate.assign_object(model, products=[site], relating_object=proj)
    aggregate.assign_object(model, products=[building], relating_object=site)
    aggregate.assign_object(model, products=[ground, upper, roof_level], relating_object=building)

    ifc_pset(model, proj, "Pset_KIN_ProjectStatus", {
        "Stage": "Concept BIM / LOD 200",
        "GrossFloorArea": 258.0,
        "NetFloorArea": 215.0,
        "FootprintWidth": 14.8,
        "FootprintDepth": 10.8,
        "ConstructionReady": False,
        "ProfessionalReviewRequired": True,
        "OpenIssues": "Site survey; geotechnical report; climate loads; local codes; structural and MEP calculations",
    })

    mats = {
        "concrete": material.add_material(model, name="Architectural concrete — light", category="Concrete"),
        "timber": material.add_material(model, name="Charred timber cladding — black", category="Wood"),
        "partition": material.add_material(model, name="Internal partition — timber frame", category="Gypsum"),
        "slab": material.add_material(model, name="Insulated concrete / timber floor assembly", category="Composite"),
        "roof": material.add_material(model, name="Standing seam metal roof — charcoal", category="Metal"),
        "glass": material.add_material(model, name="Triple insulated glazing", category="Glass"),
        "door": material.add_material(model, name="Timber door", category="Wood"),
    }

    # Native IFC presentation styles make the model readable in Bonsai,
    # instead of showing every element as an undifferentiated grey shell.
    style_specs = {
        "concrete": ((0.72, 0.73, 0.70), 0.0, 0.78, 0.0),
        "timber": ((0.035, 0.045, 0.043), 0.0, 0.62, 0.0),
        "partition": ((0.82, 0.82, 0.78), 0.0, 0.78, 0.0),
        "slab": ((0.48, 0.50, 0.48), 0.0, 0.82, 0.0),
        "roof": ((0.075, 0.090, 0.098), 0.0, 0.34, 0.48),
        "glass": ((0.18, 0.35, 0.37), 0.42, 0.12, 0.0),
        "door": ((0.52, 0.25, 0.11), 0.0, 0.52, 0.0),
    }
    for key, (colour, transparency, roughness, metallic) in style_specs.items():
        surface = style.add_style(model, name=f"KIN {key.title()} Style")
        style.add_surface_style(model, style=surface, ifc_class="IfcSurfaceStyleRendering", attributes={
            "SurfaceColour": {"Name": None, "Red": colour[0], "Green": colour[1], "Blue": colour[2]},
            "Transparency": transparency,
            "ReflectanceMethod": "NOTDEFINED",
            "DiffuseColour": {"Name": None, "Red": colour[0], "Green": colour[1], "Blue": colour[2]},
            "SpecularColour": metallic,
            "SpecularHighlight": {"SpecularRoughness": roughness},
        })
        style.assign_material_style(model, material=mats[key], style=surface, context=body)

    counters = {"wall": 0, "slab": 0, "window": 0, "door": 0, "roof": 0}

    def assign_mat(product, key):
        material.assign_material(model, products=[product], type="IfcMaterial", material=mats[key])

    def add_wall(name, x, y, z, length, height, thick, angle, storey, mat_key="partition"):
        wall = root.create_entity(model, ifc_class="IfcWall", name=name)
        rep = geometry.add_wall_representation(model, context=body, length=length, height=height, thickness=thick)
        geometry.assign_representation(model, product=wall, representation=rep)
        geometry.edit_object_placement(model, product=wall, matrix=matrix(x, y, z, angle))
        spatial.assign_container(model, products=[wall], relating_structure=storey)
        assign_mat(wall, mat_key)
        counters["wall"] += 1
        return wall

    def add_slab(name, x, y, z, polyline, depth, storey):
        slab = root.create_entity(model, ifc_class="IfcSlab", predefined_type="FLOOR", name=name)
        rep = geometry.add_slab_representation(model, context=body, depth=depth, polyline=polyline)
        geometry.assign_representation(model, product=slab, representation=rep)
        geometry.edit_object_placement(model, product=slab, matrix=matrix(x, y, z))
        spatial.assign_container(model, products=[slab], relating_structure=storey)
        assign_mat(slab, "slab")
        counters["slab"] += 1
        return slab

    def add_mesh_product(ifc_class, name, vertices, faces, storey, mat_key, predefined_type=None):
        obj = root.create_entity(model, ifc_class=ifc_class, predefined_type=predefined_type, name=name)
        rep = geometry.add_mesh_representation(model, context=body, vertices=[vertices], faces=[faces])
        geometry.assign_representation(model, product=obj, representation=rep)
        geometry.edit_object_placement(model, product=obj, matrix=matrix())
        spatial.assign_container(model, products=[obj], relating_structure=storey)
        assign_mat(obj, mat_key)
        return obj

    def add_space(code, name, area, rect, z, storey):
        x, y, w, d = rect
        space = root.create_entity(model, ifc_class="IfcSpace", predefined_type="INTERNAL", name=f"{code} {name}")
        space.LongName = name
        rep = geometry.add_slab_representation(model, context=body, depth=0.025, polyline=[(0, 0), (w, 0), (w, d), (0, d)])
        geometry.assign_representation(model, product=space, representation=rep)
        geometry.edit_object_placement(model, product=space, matrix=matrix(x, y, z + 0.01))
        aggregate.assign_object(model, products=[space], relating_object=storey)
        ifc_pset(model, space, "Pset_SpaceCommon", {"Reference": code, "IsExternal": False})
        ifc_pset(model, space, "Qto_SpaceBaseQuantities", {"NetFloorArea": area, "Height": 3.0})
        ifc_pset(model, space, "Pset_KIN_RoomData", {"ProgramArea": area, "Level": storey.Name})
        return space

    # Site and primary floor plates.
    add_slab("Ground floor insulated slab", 0, 0, -0.22, [(0, 0), (14.8, 0), (14.8, 10.8), (0, 10.8)], 0.22, ground)
    add_slab("Upper floor plate", 0, 0, 3.05, [(0, 0), (10.05, 0), (10.05, 4.0), (14.8, 4.0), (14.8, 10.8), (0, 10.8)], 0.20, upper)
    add_slab("South terrace", -0.45, -2.0, -0.10, [(0, 0), (15.7, 0), (15.7, 2.0), (0, 2.0)], 0.10, ground)

    # External envelope per gabled volume.
    outer_walls = []
    for vol in VOLUMES:
        x, y, w, d = vol["x"], vol["y"], vol["w"], vol["d"]
        finish = vol["finish"]
        outer_walls.append(add_wall(f"{vol['name']} — south", x, y, 0, w, vol["eave"], 0.28, 0, ground, finish))
        outer_walls.append(add_wall(f"{vol['name']} — north", x + w, y + d, 0, w, vol["eave"], 0.28, math.pi, ground, finish))
        outer_walls.append(add_wall(f"{vol['name']} — west", x, y + d, 0, d, vol["eave"], 0.28, -math.pi / 2, ground, finish))
        outer_walls.append(add_wall(f"{vol['name']} — east", x + w, y, 0, d, vol["eave"], 0.28, math.pi / 2, ground, finish))

    # Low concrete pavilion on the right foreground.
    pavilion_walls = [
        add_wall("Right concrete pavilion — south", 10.0, 0.60, 0, 4.8, 3.35, 0.28, 0, ground, "concrete"),
        add_wall("Right concrete pavilion — east", 14.8, 0.60, 0, 4.0, 3.35, 0.28, math.pi / 2, ground, "concrete"),
        add_wall("Right concrete pavilion — west", 10.0, 4.60, 0, 4.0, 3.35, 0.28, -math.pi / 2, ground, "concrete"),
    ]
    add_slab("Right pavilion warm roof", 10.0, 0.60, 3.35, [(0, 0), (4.8, 0), (4.8, 4.0), (0, 4.0)], 0.22, roof_level)

    # Internal partitions derived from the room program.
    for idx, yy in enumerate((4.375, 7.725), 1):
        add_wall(f"Ground partition band {idx}", 0.25, yy, 0, 14.30, 3.05, 0.14, 0, ground)
    ground_verticals = [7.25, 13.30, 4.7125, 8.85, 12.30, 4.713636, 7.772727, 9.195455, 11.709091]
    for idx, xx in enumerate(ground_verticals, 1):
        band = 0 if idx <= 2 else (1 if idx <= 5 else 2)
        y0, length = ((0.30, 4.00), (4.45, 3.20), (7.80, 2.20))[band]
        add_wall(f"Ground room divider {idx}", xx, y0, 0, length, 3.05, 0.14, math.pi / 2, ground)

    add_wall("Upper bedroom corridor wall", 0.25, 4.90, UPPER_Z, 10.20, 3.15, 0.14, 0, upper)
    for idx, xx in enumerate((4.197222, 7.369444), 1):
        add_wall(f"Upper bedroom divider {idx}", xx, 0.30, UPPER_Z, 4.50, 3.15, 0.14, math.pi / 2, upper)
    for idx, xx in enumerate((2.829545, 5.706818, 9.925, 13.120455), 1):
        add_wall(f"Upper service divider {idx}", xx, 5.00, UPPER_Z, 2.20, 3.15, 0.14, math.pi / 2, upper)
    add_wall("Upper north gallery wall", 5.40, 7.30, UPPER_Z, 8.85, 3.15, 0.14, 0, upper)
    add_wall("Upper family lounge divider", 9.808333, 7.40, UPPER_Z, 3.00, 3.15, 0.14, math.pi / 2, upper)

    for code, name, area, rect in ROOMS_GROUND:
        add_space(code, name, area, rect, GROUND_Z, ground)
    for code, name, area, rect in ROOMS_UPPER:
        add_space(code, name, area, rect, UPPER_Z, upper)

    # Close the vertical envelope above the eaves with solid gable wall prisms.
    for vol in VOLUMES:
        x, y, w, d = vol["x"], vol["y"], vol["w"], vol["d"]
        e, r, t = vol["eave"], vol["ridge"], 0.28
        finish = vol["finish"]
        front_verts = [
            (x, y, e), (x + w, y, e), (x + w / 2, y, r),
            (x, y + t, e), (x + w, y + t, e), (x + w / 2, y + t, r),
        ]
        back_verts = [
            (x, y + d - t, e), (x + w, y + d - t, e), (x + w / 2, y + d - t, r),
            (x, y + d, e), (x + w, y + d, e), (x + w / 2, y + d, r),
        ]
        prism_faces = [[0, 1, 2], [5, 4, 3], [0, 3, 4, 1], [1, 4, 5, 2], [2, 5, 3, 0]]
        front_gable = add_mesh_product("IfcWall", f"{vol['name']} — front gable wall", front_verts, prism_faces, upper, finish)
        back_gable = add_mesh_product("IfcWall", f"{vol['name']} — rear gable wall", back_verts, prism_faces, upper, finish)
        counters["wall"] += 2
        for gable in (front_gable, back_gable):
            ifc_pset(model, gable, "Pset_WallCommon", {"IsExternal": True, "LoadBearing": False, "Reference": "Insulated gable wall"})

    # Roof meshes: two closed solid leaves per gable, 180 mm deep.
    for vol in VOLUMES:
        x, y, w, d = vol["x"], vol["y"], vol["w"], vol["d"]
        e, r, t = vol["eave"], vol["ridge"], 0.18
        top_left = [
            (x - 0.25, y - 0.25, e), (x + w / 2, y - 0.25, r),
            (x + w / 2, y + d + 0.25, r), (x - 0.25, y + d + 0.25, e),
        ]
        top_right = [
            (x + w / 2, y - 0.25, r), (x + w + 0.25, y - 0.25, e),
            (x + w + 0.25, y + d + 0.25, e), (x + w / 2, y + d + 0.25, r),
        ]
        verts = []
        faces = []
        for leaf in (top_left, top_right):
            base = len(verts)
            verts.extend(leaf)
            verts.extend([(px, py, pz - t) for px, py, pz in leaf])
            faces.extend([
                [base + 0, base + 1, base + 2, base + 3],
                [base + 7, base + 6, base + 5, base + 4],
                [base + 0, base + 4, base + 5, base + 1],
                [base + 1, base + 5, base + 6, base + 2],
                [base + 2, base + 6, base + 7, base + 3],
                [base + 3, base + 7, base + 4, base + 0],
            ])
        roof = add_mesh_product("IfcRoof", f"{vol['name']} standing-seam roof", verts, faces, roof_level, "roof", "GABLE_ROOF")
        counters["roof"] += 1
        ifc_pset(model, roof, "Pset_RoofCommon", {"IsExternal": True, "Reference": "Metal standing seam 180mm assembly"})

    # Openings and fillings in the primary south facades.
    def opening_filling(wall, name, cls, x, y, z, width, height, angle, storey, mat_key):
        opening = root.create_entity(model, ifc_class="IfcOpeningElement", name=f"Opening for {name}")
        orepr = geometry.add_wall_representation(model, context=body, length=width, height=height, thickness=0.38)
        geometry.assign_representation(model, product=opening, representation=orepr)
        geometry.edit_object_placement(model, product=opening, matrix=matrix(x, y, z, angle))
        feature.add_feature(model, feature=opening, element=wall)
        filling = root.create_entity(model, ifc_class=cls, name=name)
        frepr = geometry.add_wall_representation(model, context=body, length=width, height=height, thickness=0.10)
        geometry.assign_representation(model, product=filling, representation=frepr)
        geometry.edit_object_placement(model, product=filling, matrix=matrix(x, y + 0.09, z, angle))
        spatial.assign_container(model, products=[filling], relating_structure=storey)
        feature.add_filling(model, opening=opening, element=filling)
        assign_mat(filling, mat_key)
        ifc_pset(model, filling, "Pset_KIN_Opening", {"Width": width, "Height": height, "TripleGlazed": cls == "IfcWindow"})
        counters["window" if cls == "IfcWindow" else "door"] += 1
        return filling

    left_south = outer_walls[0]
    center_south = outer_walls[4]
    right_pavilion_south = pavilion_walls[0]
    opening_filling(left_south, "W01 Living panorama", "IfcWindow", 0.45, 0.0, 0.15, 3.95, 2.55, 0, ground, "glass")
    opening_filling(left_south, "W02 Upper studio", "IfcWindow", 2.70, 0.0, 3.55, 1.65, 2.20, 0, upper, "glass")
    opening_filling(center_south, "D01 Main entrance", "IfcDoor", 5.55, 0.0, 0.05, 1.05, 2.45, 0, ground, "door")
    opening_filling(center_south, "W03 Double-height slot", "IfcWindow", 7.18, 0.0, 0.70, 0.78, 5.15, 0, ground, "glass")
    opening_filling(right_pavilion_south, "W04 Flexible room", "IfcWindow", 11.55, 0.60, 0.18, 1.48, 2.62, 0, ground, "glass")
    opening_filling(right_pavilion_south, "D02 Terrace door", "IfcDoor", 13.45, 0.60, 0.08, 0.95, 2.50, 0, ground, "glass")

    # A few side/rear openings for daylight and cross-ventilation.
    opening_filling(outer_walls[2], "W05 West living", "IfcWindow", 0.0, 6.20, 0.75, 2.20, 1.65, -math.pi / 2, ground, "glass")
    opening_filling(outer_walls[6], "W06 Stair north light", "IfcWindow", 5.0, 9.30, 3.70, 1.10, 1.80, -math.pi / 2, upper, "glass")
    opening_filling(outer_walls[8], "W07 Family lounge", "IfcWindow", 10.70, 4.0, 3.65, 1.55, 1.95, 0, upper, "glass")

    # External site proxy makes the unknown site condition explicit.
    terrain = add_mesh_product(
        "IfcGeographicElement", "Concept terrain — replace with survey",
        [(-18, -14, -0.28), (32, -14, -0.20), (32, 28, -0.55), (-18, 28, -0.35)],
        [[0, 1, 2, 3]], site, "slab", "TERRAIN",
    )
    ifc_pset(model, terrain, "Pset_KIN_Assumption", {"Source": "Photographic inference only", "SurveyRequired": True})

    model.write(str(path))
    return counters


# ----------------------------- Blender visualization -----------------------------


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        pass


def make_material(name, base, roughness=0.55, metallic=0.0, emission=None, emission_strength=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*base, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def bevel(obj, amount=0.035, segments=3):
    mod = obj.modifiers.new("Soft construction edges", "BEVEL")
    mod.width = amount
    mod.segments = segments


def box(name, size, loc, mat, rotation=(0, 0, 0), bevel_size=0.025, collection=None):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        obj.data.materials.append(mat)
    if bevel_size:
        bevel(obj, bevel_size)
    if collection and obj.name not in collection.objects:
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        collection.objects.link(obj)
    return obj


def mesh_obj(name, verts, faces, mat, collection=None, bevel_size=0.015):
    mesh = bpy.data.meshes.new(name + " Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    (collection or bpy.context.scene.collection).objects.link(obj)
    if mat:
        obj.data.materials.append(mat)
    if bevel_size:
        bevel(obj, bevel_size, 2)
    return obj


def look_at(obj, target):
    direction = np.array(target) - np.array(obj.location)
    obj.rotation_euler = direction.tolist()
    obj.rotation_euler = direction_to_euler(direction)


def direction_to_euler(direction):
    from mathutils import Vector
    return Vector(direction).to_track_quat("-Z", "Y").to_euler()


def create_camera(name, location, target, lens=46, ortho=None):
    data = bpy.data.cameras.new(name)
    camera = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = location
    camera.rotation_euler = direction_to_euler(np.array(target) - np.array(location))
    data.lens = lens
    if ortho:
        data.type = "ORTHO"
        data.ortho_scale = ortho
    return camera


def facade_cells(name, axis, origin, length, height, thickness, openings, mat, collection):
    cuts = {0.0, float(length)}
    for op in openings:
        cuts.add(op[0]); cuts.add(op[1])
    cuts = sorted(cuts)
    created = []
    for i in range(len(cuts) - 1):
        u0, u1 = cuts[i], cuts[i + 1]
        um = (u0 + u1) / 2
        active = [op for op in openings if op[0] < um < op[1]]
        zcuts = {0.0, float(height)}
        for op in active:
            zcuts.add(op[2]); zcuts.add(op[3])
        zcuts = sorted(zcuts)
        for j in range(len(zcuts) - 1):
            z0, z1 = zcuts[j], zcuts[j + 1]
            zm = (z0 + z1) / 2
            if any(op[2] < zm < op[3] for op in active):
                continue
            if u1 - u0 < 0.01 or z1 - z0 < 0.01:
                continue
            if axis == "x":
                loc = (origin[0] + (u0 + u1) / 2, origin[1], origin[2] + (z0 + z1) / 2)
                size = (u1 - u0, thickness, z1 - z0)
            else:
                loc = (origin[0], origin[1] + (u0 + u1) / 2, origin[2] + (z0 + z1) / 2)
                size = (thickness, u1 - u0, z1 - z0)
            created.append(box(f"{name} panel {i:02d}-{j:02d}", size, loc, mat, bevel_size=0.002, collection=collection))
    return created


def glazing(name, axis, origin, opening, glass, glow, collection, frames=True):
    u0, u1, z0, z1 = opening
    width, height = u1 - u0, z1 - z0
    if axis == "x":
        loc = (origin[0] + (u0 + u1) / 2, origin[1] - 0.02, origin[2] + (z0 + z1) / 2)
        pane = box(name + " glass", (width - 0.05, 0.065, height - 0.05), loc, glass, bevel_size=0.01, collection=collection)
        box(name + " warm interior", (width - 0.12, 0.035, height - 0.12), (loc[0], loc[1] + 0.07, loc[2]), glow, bevel_size=0.0, collection=collection)
        if frames:
            frame_t = 0.055
            for xx in (loc[0] - width / 2, loc[0] + width / 2):
                box(name + " jamb", (frame_t, 0.11, height), (xx, loc[1] - 0.02, loc[2]), metal, bevel_size=0.006, collection=collection)
            for zz in (loc[2] - height / 2, loc[2] + height / 2):
                box(name + " rail", (width, 0.11, frame_t), (loc[0], loc[1] - 0.02, zz), metal, bevel_size=0.006, collection=collection)
    else:
        loc = (origin[0] - 0.02, origin[1] + (u0 + u1) / 2, origin[2] + (z0 + z1) / 2)
        pane = box(name + " glass", (0.065, width - 0.05, height - 0.05), loc, glass, bevel_size=0.01, collection=collection)
    return pane


def roof_pair(vol, mat, trim_mat, collection, detail_collection):
    x, y, w, d = vol["x"], vol["y"], vol["w"], vol["d"]
    e, r = vol["eave"], vol["ridge"]
    t = 0.16
    overhang = 0.24
    leaves = [
        [(x - overhang, y - overhang, e), (x + w / 2, y - overhang, r),
         (x + w / 2, y + d + overhang, r), (x - overhang, y + d + overhang, e)],
        [(x + w / 2, y - overhang, r), (x + w + overhang, y - overhang, e),
         (x + w + overhang, y + d + overhang, e), (x + w / 2, y + d + overhang, r)],
    ]
    for side, leaf in zip(("left", "right"), leaves):
        verts = leaf + [(px, py, pz - t) for px, py, pz in leaf]
        faces = [
            (0, 1, 2, 3), (7, 6, 5, 4),
            (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0),
        ]
        mesh_obj(f"{vol['name']} {side} solid roof", verts, faces, mat, collection, 0.004)

    # Clean ridge and eave lines prevent the crossed, protruding roof edges of v1.1.
    box(vol["name"] + " ridge cap", (0.11, d + 0.48, 0.10),
        (x + w / 2, y + d / 2, r + 0.035), trim_mat,
        bevel_size=0.018, collection=detail_collection)
    for gutter_x, side in ((x - overhang + 0.02, "left"), (x + w + overhang - 0.02, "right")):
        box(vol["name"] + f" {side} eave trim", (0.09, d + 0.48, 0.12),
            (gutter_x, y + d / 2, e - 0.035), trim_mat,
            bevel_size=0.012, collection=detail_collection)


def gable_face(name, x, y, w, eave, ridge, depth, mat, collection, front=True):
    yy = y - depth / 2 if front else y + depth / 2
    verts = [(x, yy, eave), (x + w, yy, eave), (x + w / 2, yy, ridge),
             (x, yy + depth, eave), (x + w, yy + depth, eave), (x + w / 2, yy + depth, ridge)]
    faces = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    return mesh_obj(name, verts, faces, mat, collection, 0.01)


def build_blender_scene(blend_path: Path, render_dir: Path):
    clear_scene()
    global concrete, timber, roof_mat, glass, glow, metal
    concrete = make_material("Light architectural concrete", (0.58, 0.59, 0.57), 0.78)
    timber = make_material("Charred vertical timber", (0.025, 0.032, 0.035), 0.66)
    roof_mat = make_material("Charcoal standing seam", (0.055, 0.065, 0.072), 0.34, 0.55)
    glass = make_material("Dark low-e glass", (0.025, 0.060, 0.064), 0.14, 0.03, emission=(0.34, 0.11, 0.025), emission_strength=0.16)
    glass_bsdf = glass.node_tree.nodes.get("Principled BSDF")
    glass_bsdf.inputs["Transmission Weight"].default_value = 0.34
    glass_bsdf.inputs["IOR"].default_value = 1.45
    glow = make_material("Warm interior glow", (0.32, 0.14, 0.035), 0.38, emission=(1.0, 0.28, 0.055), emission_strength=5.2)
    metal = make_material("Window frames", (0.018, 0.021, 0.022), 0.25, 0.65)
    deck_mat = make_material("Weathered terrace timber", (0.20, 0.145, 0.095), 0.75)
    ground_mat = make_material("Wet volcanic ground", (0.035, 0.043, 0.040), 0.96)
    path_mat = make_material("Stone steps", (0.28, 0.29, 0.28), 0.84)
    grass_mat = make_material("Mountain moss", (0.065, 0.12, 0.075), 0.90)

    envelope = bpy.data.collections.new("01_Envelope")
    roofs = bpy.data.collections.new("02_Roofs")
    glazing_col = bpy.data.collections.new("03_Windows_Doors")
    site_col = bpy.data.collections.new("04_Site")
    detail_col = bpy.data.collections.new("05_Details")
    for col in (envelope, roofs, glazing_col, site_col, detail_col):
        bpy.context.scene.collection.children.link(col)

    # Terrain: intentionally conceptual, irregular and dark like the reference landscape.
    size = 42
    verts, faces = [], []
    grid = 22
    for iy in range(grid + 1):
        for ix in range(grid + 1):
            xx = -13 + size * ix / grid
            yy = -13 + size * iy / grid
            rr = math.hypot(xx - 7.4, yy - 5.0)
            zz = -0.36 + 0.018 * math.sin(ix * 1.7) + 0.025 * math.cos(iy * 1.4) + max(rr - 11, 0) * 0.035
            verts.append((xx, yy, zz))
    for iy in range(grid):
        for ix in range(grid):
            a = iy * (grid + 1) + ix
            faces.append((a, a + 1, a + grid + 2, a + grid + 1))
    mesh_obj("Concept mountain terrain", verts, faces, ground_mat, site_col, 0)
    box("South timber terrace", (15.6, 2.25, 0.16), (7.4, -1.12, 0.00), deck_mat, bevel_size=0.04, collection=site_col)
    for i in range(11):
        box(f"Terrace board {i:02d}", (15.45, 0.025, 0.018), (7.4, -2.10 + i * 0.20, 0.095), path_mat, bevel_size=0.003, collection=detail_col)
    for i in range(4):
        box(f"Entrance step {i}", (2.10 - i * 0.18, 0.44, 0.14), (7.55, -2.25 - i * 0.34, -0.01 - i * 0.08), path_mat, bevel_size=0.025, collection=site_col)

    # Main wall fields with the front openings cut as actual geometry.
    left_ops = [(0.45, 4.40, 0.15, 2.70), (2.70, 4.35, 3.55, 5.75)]
    center_ops = [(0.55, 1.60, 0.05, 2.50), (2.18, 2.96, 0.70, 5.85)]
    pavilion_ops = [(1.55, 3.03, 0.18, 2.80), (3.45, 4.40, 0.08, 2.58)]
    right_rear_ops = [(0.78, 2.18, 3.68, 5.62)]
    facade_cells("Left south", "x", (0, 0, 0), 5.15, 6.45, 0.28, left_ops, concrete, envelope)
    facade_cells("Center south", "x", (5.0, 0, 0), 5.05, 6.70, 0.30, center_ops, timber, envelope)
    facade_cells("Right pavilion south", "x", (10.0, 0.60, 0), 4.8, 3.35, 0.28, pavilion_ops, concrete, envelope)
    facade_cells("Right rear south", "x", (10.0, 4.00, 0), 4.8, 6.15, 0.28, right_rear_ops, timber, envelope)

    glazing("W01 Living panorama", "x", (0, 0, 0), left_ops[0], glass, glow, glazing_col)
    glazing("W02 Upper studio", "x", (0, 0, 0), left_ops[1], glass, glow, glazing_col)
    glazing("D01 Main entrance", "x", (5.0, 0, 0), center_ops[0], glass, glow, glazing_col)
    glazing("W03 Double-height slot", "x", (5.0, 0, 0), center_ops[1], glass, glow, glazing_col)
    glazing("W04 Flexible room", "x", (10.0, 0.60, 0), pavilion_ops[0], glass, glow, glazing_col)
    glazing("D02 Terrace door", "x", (10.0, 0.60, 0), pavilion_ops[1], glass, glow, glazing_col)
    glazing("W07 Family lounge", "x", (10.0, 4.00, 0), right_rear_ops[0], glass, glow, glazing_col)

    # Side and rear walls.
    for vol in VOLUMES:
        mat = concrete if vol["finish"] == "concrete" else timber
        x, y, w, d, e = vol["x"], vol["y"], vol["w"], vol["d"], vol["eave"]
        box(vol["name"] + " north wall", (w, 0.28, e), (x + w / 2, y + d, e / 2), mat, bevel_size=0.0, collection=envelope)
        box(vol["name"] + " west wall", (0.28, d, e), (x, y + d / 2, e / 2), mat, bevel_size=0.0, collection=envelope)
        box(vol["name"] + " east wall", (0.28, d, e), (x + w, y + d / 2, e / 2), mat, bevel_size=0.0, collection=envelope)
        gable_face(vol["name"] + " front gable", x, y, w, e, vol["ridge"], 0.28, mat, envelope, True)
        gable_face(vol["name"] + " rear gable", x, y + d, w, e, vol["ridge"], 0.28, mat, envelope, False)
        roof_pair(vol, roof_mat, metal, roofs, detail_col)

    # Low foreground pavilion shell and parapet roof.
    box("Right pavilion east wall", (0.28, 3.40, 3.35), (14.8, 2.30, 1.675), concrete, bevel_size=0.0, collection=envelope)
    box("Right pavilion west return", (0.28, 3.40, 3.35), (10.0, 2.30, 1.675), concrete, bevel_size=0.0, collection=envelope)
    box("Right pavilion flat roof", (5.06, 4.18, 0.24), (12.40, 2.60, 3.43), concrete, bevel_size=0.006, collection=roofs)
    box("Right pavilion south parapet", (5.04, 0.13, 0.22), (12.40, 0.51, 3.64), concrete, bevel_size=0.004, collection=detail_col)
    box("Right pavilion east parapet", (0.13, 3.55, 0.22), (14.87, 2.28, 3.64), concrete, bevel_size=0.004, collection=detail_col)

    # Window mullions and readable vertical timber rhythm.
    for x in np.linspace(0.55, 4.30, 5):
        box("Living mullion", (0.045, 0.13, 2.55), (x, -0.08, 1.425), metal, bevel_size=0.004, collection=detail_col)
    for xx in np.arange(5.18, 9.95, 0.22):
        box("Charred timber batten", (0.024, 0.035, 6.45), (xx, -0.17, 3.23), metal, bevel_size=0.0, collection=detail_col)
    for xx in np.arange(10.18, 14.72, 0.22):
        if not (10.72 < xx < 12.24):
            box("Right rear timber batten", (0.024, 0.035, 2.70), (xx, 3.83, 4.82), metal, bevel_size=0.0, collection=detail_col)

    # Door levers and refined mullions make openings read as real components.
    for name, location in (("Main entrance lever", (6.45, -0.115, 1.15)), ("Terrace door lever", (14.30, 0.485, 1.12))):
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.028, depth=0.10, location=location, rotation=(math.pi / 2, 0, 0))
        handle = bpy.context.object
        handle.name = name
        handle.data.materials.append(metal)
        for current in list(handle.users_collection):
            current.objects.unlink(handle)
        detail_col.objects.link(handle)

    # Warm interiors behind the windows, with a few restrained furniture silhouettes.
    box("Living floor", (4.55, 5.4, 0.10), (2.55, 2.8, 0.10), deck_mat, bevel_size=0.01, collection=detail_col)
    box("Dining table", (2.15, 0.92, 0.10), (2.65, 1.55, 0.80), deck_mat, bevel_size=0.035, collection=detail_col)
    for xx in (1.85, 3.45):
        for yy in (1.10, 2.00):
            box("Dining chair", (0.45, 0.45, 0.62), (xx, yy, 0.48), metal, bevel_size=0.04, collection=detail_col)
    box("Kitchen island", (2.45, 0.82, 0.88), (8.00, 2.10, 0.49), concrete, bevel_size=0.04, collection=detail_col)

    # Sparse rocks and moss tufts around the house.
    for i, (xx, yy, sc) in enumerate([
        (-2.4, -3.5, 0.85), (18.2, -1.8, 1.1), (19.5, 5.0, 0.75), (-4.0, 8.5, 1.2),
        (16.0, 12.0, 1.35), (2.0, 15.0, 0.95), (10.0, -5.0, 0.55), (22.0, 13.0, 1.4),
    ]):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=sc, location=(xx, yy, -0.12 + sc * 0.25))
        rock = bpy.context.object
        rock.name = f"Landscape rock {i:02d}"
        rock.scale = (1.4, 0.9, 0.52)
        rock.data.materials.append(path_mat if i % 2 else grass_mat)
        for c in list(rock.users_collection): c.objects.unlink(rock)
        site_col.objects.link(rock)

    # Lighting for a cool overcast exterior with warm inhabited windows.
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.055, 0.075, 0.095, 1)
    bg.inputs["Strength"].default_value = 0.44
    sun_data = bpy.data.lights.new("Cloud-filtered sun", "SUN")
    sun_data.energy = 3.0
    sun_data.angle = math.radians(18)
    sun = bpy.data.objects.new("Cloud-filtered sun", sun_data)
    bpy.context.scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(28), math.radians(-20), math.radians(-35))
    area_data = bpy.data.lights.new("Front softbox", "AREA")
    area_data.energy = 1650
    area_data.shape = "DISK"
    area_data.size = 12
    area = bpy.data.objects.new("Front softbox", area_data)
    bpy.context.scene.collection.objects.link(area)
    area.location = (7.5, -11, 13)
    area.rotation_euler = direction_to_euler(np.array((7.5, 2.5, 3.5)) - np.array(area.location))

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.quality = 90
    scene.render.film_transparent = False
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.resolution_percentage = 100

    hero = create_camera("Camera Hero", (19.0, -29.5, 9.6), (7.25, 3.25, 4.0), lens=55)
    scene.camera = hero
    render_dir.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(render_dir / "exterior-hero.jpg")
    bpy.ops.render.render(write_still=True)

    axon = create_camera("Camera Axonometric", (-15.5, -19.0, 20.5), (7.4, 4.4, 3.7), lens=55)
    scene.camera = axon
    scene.render.filepath = str(render_dir / "axonometric.jpg")
    bpy.ops.render.render(write_still=True)

    elev = create_camera("Camera South Elevation", (7.4, -33.0, 4.45), (7.4, 2.2, 4.45), lens=58, ortho=18.5)
    scene.camera = elev
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.filepath = str(render_dir / "south-elevation.jpg")
    bpy.ops.render.render(write_still=True)

    scene.camera = hero
    scene["ProjectStage"] = "Concept BIM / LOD 200"
    scene["NetFloorArea_m2"] = 215.0
    scene["GrossFloorArea_m2"] = 258.0
    scene["ProfessionalReviewRequired"] = True
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)

    # Portable 3D preview for the browser. Lights/cameras are deliberately excluded.
    bpy.ops.object.select_all(action="DESELECT")
    for col in (envelope, roofs, glazing_col, detail_col):
        for obj in col.objects:
            if obj.type == "MESH": obj.select_set(True)
    for obj in site_col.objects:
        if obj.type == "MESH" and (obj.name.startswith("South timber terrace") or obj.name.startswith("Entrance step")):
            obj.select_set(True)
    bpy.context.view_layer.objects.active = next((o for o in bpy.context.selected_objects if o.type == "MESH"), None)
    bpy.ops.export_scene.gltf(filepath=str(OUT / "kin-house.glb"), export_format="GLB", use_selection=True, export_yup=True)


def validate_ifc(path: Path):
    model = ifcopenshell.open(str(path))
    areas = []
    for space in model.by_type("IfcSpace"):
        for rel in getattr(space, "IsDefinedBy", []) or []:
            definition = rel.RelatingPropertyDefinition
            if definition and definition.is_a("IfcPropertySet") and definition.Name == "Qto_SpaceBaseQuantities":
                for prop in definition.HasProperties:
                    if prop.Name == "NetFloorArea":
                        areas.append(float(prop.NominalValue.wrappedValue))
    report = {
        "ifc_schema": model.schema,
        "spaces": len(model.by_type("IfcSpace")),
        "walls": len(model.by_type("IfcWall")),
        "slabs": len(model.by_type("IfcSlab")),
        "roofs": len(model.by_type("IfcRoof")),
        "windows": len(model.by_type("IfcWindow")),
        "doors": len(model.by_type("IfcDoor")),
        "net_area": round(sum(areas), 2),
    }
    if report["spaces"] != 21 or abs(report["net_area"] - 215.0) > 0.01:
        raise RuntimeError(f"Room program validation failed: {report}")
    return report


if __name__ == "__main__":
    ifc_path = OUT / "kin-house.ifc"
    blend_path = OUT / "kin-house.blend"
    counters = build_ifc(ifc_path)
    build_blender_scene(blend_path, OUT / "renders")
    report = validate_ifc(ifc_path)
    print("KIN_HOUSE_IFC", ifc_path)
    print("KIN_HOUSE_BLEND", blend_path)
    print("KIN_HOUSE_REPORT", report)
    print("KIN_HOUSE_COUNTERS", counters)
