import bpy

# Make renders crisp and saturated instead of dim and hazy.
# - Blender's default AgX view transform desaturates and flattens bright
#   colors; Standard shows the material colors as they are.
# - The detector is hundreds of overlapping, nearly transparent pieces, so
#   looking through it stacks up into a haze. Lower its opacity
#   (0 hides it completely).

VIEW_TRANSFORM = 'Standard'
DETECTOR = "Detector"
DETECTOR_ALPHA = 0.003    # iSpy exports use 0.01


scene = bpy.context.scene
scene.view_settings.view_transform = VIEW_TRANSFORM
scene.view_settings.look = 'None'
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0

count = 0
root = bpy.data.objects.get(DETECTOR)
if root is not None:
    materials = {s.material for o in root.children_recursive
                 for s in o.material_slots if s.material}
    for m in materials:
        bsdf = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdf is None or bsdf.inputs["Alpha"].is_linked:
            continue
        bsdf.inputs["Alpha"].default_value = DETECTOR_ALPHA
        m.diffuse_color[3] = DETECTOR_ALPHA
        m.surface_render_method = 'BLENDED'
        count += 1

print(f"View transform: {VIEW_TRANSFORM}; detector alpha {DETECTOR_ALPHA} on {count} materials")
