import bpy

# Add a bloom (glow) effect to chosen objects, such as photons, electrons,
# muons, and jets. Other objects don't glow.
# Each chosen object's material writes its color to a "glow" render pass
# (an AOV); the compositor blooms only that pass and adds it on top of the
# render. Works with EEVEE and Cycles (Blender 5.x).
# Run it last, after fix_objects.py and principled_materials.py, since
# those rebuild materials. Safe to run more than once.
# To see the glow in the viewport, use Rendered shading with
# Viewport Shading > Compositor set to Always.

# ---- Settings ----
# Objects that glow, matched by name prefix without the version number:
# name prefix -> glow strength (large objects like jets need less)
GLOW = {
    "Photons_V": 4.0,
    "GsfElectrons_V": 4.0,
    "GlobalMuons_V": 4.0,
    "PATJets_V": 1.0,
}
SIZE = 0.8          # how far the glow spreads (0-1)

AOV = "glow"
AOV_NODE = "Glow AOV"
GROUP = "Bloom"


def add_glow(mat, strength):
    # Write the material's color, times the strength, to the glow pass
    nt = mat.node_tree
    node = nt.nodes.get(AOV_NODE) or nt.nodes.new("ShaderNodeOutputAOV")
    node.name = node.label = AOV_NODE
    node.aov_name = AOV
    node.inputs["Color"].default_value = (*(c * strength for c in mat.diffuse_color[:3]), 1.0)
    # EEVEE's Blended transparency doesn't write render passes; Dithered
    # does, and still shows transparency
    mat.surface_render_method = 'DITHERED'


def compositor():
    # Render Layers: image + Glare (bloom) of the glow pass -> output
    ng = bpy.data.node_groups.get(GROUP)
    if ng is not None:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(GROUP, "CompositorNodeTree")
    ng.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    n, link = ng.nodes, ng.links.new

    rl = n.new("CompositorNodeRLayers")
    glare = n.new("CompositorNodeGlare")
    glare.inputs["Type"].default_value = 'Bloom'
    glare.inputs["Quality"].default_value = 'High'
    glare.inputs["Threshold"].default_value = 0.0
    glare.inputs["Strength"].default_value = 1.0
    glare.inputs["Size"].default_value = SIZE
    add = n.new("ShaderNodeMix")
    add.data_type = 'RGBA'
    add.blend_type = 'ADD'
    add.inputs["Factor"].default_value = 1.0
    out = n.new("NodeGroupOutput")

    link(rl.outputs[AOV], glare.inputs["Image"])
    link(rl.outputs["Image"], add.inputs[6])         # A
    link(glare.outputs["Glare"], add.inputs[7])      # B
    link(add.outputs[2], out.inputs["Image"])
    return ng


scene = bpy.context.scene
for vl in scene.view_layers:
    if AOV not in vl.aovs:
        aov = vl.aovs.add()
        aov.name = AOV
        aov.type = 'COLOR'

for prefix, strength in GLOW.items():
    mats = {s.material for o in bpy.data.objects if o.name.startswith(prefix)
            for s in o.material_slots if s.material}
    for mat in mats:
        add_glow(mat, strength)
    print(f"{prefix}: glow on {len(mats)} materials")

scene.compositing_node_group = compositor()
print(f"Bloom compositor set up ({GROUP})")
