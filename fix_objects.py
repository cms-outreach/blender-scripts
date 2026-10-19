import bpy

# Render the line objects of an event (tracks, muons, electrons, photons,
# and the MET arrow shaft) as tubes. Photons are dashed.
# Each tube uses its object's own material from the glb file, made flat
# (unlit, same color and transparency) unless principled_materials.py has
# already made it lit; run principled_materials.py to make them lit.
# Only line objects (edge-only meshes and curves) are styled, so solid
# shapes like the MET arrowhead, towers, and jets render as they are.
# Objects are matched by name prefix without the version number, so
# "Tracks_V" matches Tracks_V3, Tracks_V4, ...
# Uses a Geometry Nodes modifier instead of converting objects, so it works
# directly on the imported edge meshes (and on curves) and is safe to run
# more than once. Replaces the modifiers added by the earlier tracks.py,
# muons.py, electrons.py, met.py, restore_curves.py, tracks_tubes.py, and
# photons_dotted.py.

# ---- Settings (scene units are metres) ----
RESOLUTION = 16       # sides around each tube

# name prefix -> tube radius
STYLES = {
    "Tracks_V": 0.003,
    "GlobalMuons_V": 0.008,
    "GsfElectrons_V": 0.005,
    "PFMETs_V": 0.03,
    "Photons_V": 0.01,
}

# name prefix -> (dash length, gap length)
DASHED = {
    "Photons_V": (0.04, 0.03),
}

MODIFIER = "ParticleStyle"
OLD_MODIFIERS = {MODIFIER, "TubeStyle", "TrackStyle", "PhotonStyle"}


def make_flat(mat):
    # Replace a lit material with emission mixed with transparency, keeping
    # its color and alpha. Materials that are already flat, or that
    # principled_materials.py made lit, are left alone.
    if mat.get("principled"):
        return
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None:
        return
    color = tuple(bsdf.inputs["Base Color"].default_value)
    alpha = bsdf.inputs["Alpha"].default_value
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = color
    em.inputs["Strength"].default_value = 1.0
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = alpha
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    mat.diffuse_color = (*color[:3], alpha)
    mat.surface_render_method = 'BLENDED' if alpha < 1.0 else 'DITHERED'


def set_mode(node, value):
    """Works whether the node's mode is a property or a menu socket."""
    try:
        node.mode = value.upper()
    except (AttributeError, TypeError):
        node.inputs["Mode"].default_value = value


def style_group(name, radius, dash=None):
    # Geometry Nodes: edges -> curve -> solid tube, or a row of dashes,
    # with the material given to the modifier (the object's own material)
    old = bpy.data.node_groups.get(name + "_Style")
    if old is not None:
        bpy.data.node_groups.remove(old)
    ng = bpy.data.node_groups.new(name + "_Style", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Material", in_out='INPUT', socket_type='NodeSocketMaterial')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n, link = ng.nodes, ng.links.new

    gin, gout = n.new("NodeGroupInput"), n.new("NodeGroupOutput")
    m2c = n.new("GeometryNodeMeshToCurve")      # the imported edge meshes
    join = n.new("GeometryNodeJoinGeometry")    # ...and objects that are already curves
    link(gin.outputs[0], m2c.inputs["Mesh"])
    link(m2c.outputs["Curve"], join.inputs[0])
    link(gin.outputs[0], join.inputs[0])

    if dash is None:
        profile = n.new("GeometryNodeCurvePrimitiveCircle")
        profile.inputs["Resolution"].default_value = RESOLUTION
        profile.inputs["Radius"].default_value = radius
        c2m = n.new("GeometryNodeCurveToMesh")
        c2m.inputs["Fill Caps"].default_value = True
        link(join.outputs[0], c2m.inputs["Curve"])
        link(profile.outputs["Curve"], c2m.inputs["Profile Curve"])
        geometry = c2m.outputs["Mesh"]
    else:
        length, gap = dash
        c2p = n.new("GeometryNodeCurveToPoints")
        set_mode(c2p, "Length")
        c2p.inputs["Length"].default_value = length + gap
        cyl = n.new("GeometryNodeMeshCylinder")
        cyl.inputs["Vertices"].default_value = RESOLUTION
        cyl.inputs["Radius"].default_value = radius
        cyl.inputs["Depth"].default_value = length
        align = n.new("FunctionNodeAlignRotationToVector")   # point each dash along the line
        align.axis = 'Z'
        inst = n.new("GeometryNodeInstanceOnPoints")
        real = n.new("GeometryNodeRealizeInstances")
        link(join.outputs[0], c2p.inputs["Curve"])
        link(c2p.outputs["Tangent"], align.inputs["Vector"])
        link(c2p.outputs["Points"], inst.inputs["Points"])
        link(cyl.outputs["Mesh"], inst.inputs["Instance"])
        link(align.outputs["Rotation"], inst.inputs["Rotation"])
        link(inst.outputs["Instances"], real.inputs["Geometry"])
        geometry = real.outputs["Geometry"]

    smooth = n.new("GeometryNodeSetShadeSmooth")
    setm = n.new("GeometryNodeSetMaterial")
    link(geometry, smooth.inputs["Geometry"])
    link(smooth.outputs["Geometry"], setm.inputs["Geometry"])
    link(gin.outputs["Material"], setm.inputs["Material"])
    link(setm.outputs["Geometry"], gout.inputs[0])
    return ng


def set_input(mod, identifier, value):
    """Set a Geometry Nodes modifier input (Blender 5.x, then 4.x API)."""
    if hasattr(mod, "properties"):
        getattr(mod.properties.inputs, identifier).value = value
    else:
        mod[identifier] = value


def is_line(o):
    if o.type == 'CURVE':
        return True
    return o.type == 'MESH' and len(o.data.polygons) == 0 and len(o.data.edges) > 0


def restyle(name, ng):
    material_input = ng.interface.items_tree["Material"].identifier
    count = 0
    for o in [o for o in bpy.data.objects if o.name.startswith(name) and is_line(o)]:
        if o.type == 'CURVE':
            o.data.bevel_depth = 0.0   # the modifier makes the tube
        for m in [m for m in o.modifiers if m.name in OLD_MODIFIERS]:
            o.modifiers.remove(m)
        mod = o.modifiers.new(MODIFIER, 'NODES')
        mod.node_group = ng
        mat = next((s.material for s in o.material_slots if s.material), None)
        if mat is not None:
            make_flat(mat)
            set_input(mod, material_input, mat)
        count += 1
    print(f"{name}: restyled {count} objects")


for name, radius in STYLES.items():
    restyle(name, style_group(name, radius, DASHED.get(name)))
