import bpy

# Make imported detector geometry (such as muon-2.glb) render cleanly with
# the lights from add_lights.py: every material under the chosen root
# objects becomes opaque and non-metallic.
# The glTF importer gives these see-through (Blended) materials, which
# EEVEE draws in the wrong order where boxes are nested, and Metallic 0.5,
# which reflects the dark world instead of the lights.
# Safe to run more than once.

# Root objects of the imported geometry (a glb's root is named after the file)
ROOTS = ["muon-2"]

METALLIC = 0.0
ROUGHNESS = 0.5


def make_opaque(mat):
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None) if nt else None
    if bsdf is None:
        return False
    bsdf.inputs["Alpha"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = METALLIC
    bsdf.inputs["Roughness"].default_value = ROUGHNESS
    mat.diffuse_color[3] = 1.0
    mat.surface_render_method = 'DITHERED'   # opaque, drawn in depth order
    mat["principled"] = True                  # lit; left alone by the other scripts
    return True


for name in ROOTS:
    root = bpy.data.objects.get(name)
    if root is None:
        print(f"{name}: not found")
        continue
    materials = {s.material for o in [root, *root.children_recursive]
                 for s in o.material_slots if s.material}
    count = sum(make_opaque(m) for m in materials)
    print(f"{name}: made {count} materials opaque")
