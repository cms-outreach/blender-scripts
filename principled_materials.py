import bpy

# Set up the lit Principled BSDF materials, so that objects respond to
# lights and shading:
# - Solid objects (calorimeter towers, jets) get one of the named
#   materials below.
# - Every other flat (emission / unlit) material in the scene is converted,
#   such as those created by the glTF importer (iSpy exports) and the flat
#   tube materials from fix_objects.py. The color and alpha are kept,
#   including any texture or vertex color feeding them.
#   Materials that already use a lit shader are left alone.
# Objects are matched by name prefix without the version number.
# Every lit material is marked, so that fix_objects.py, run before or after
# this script, keeps it lit.

# material name -> (color, opacity, emission)
# opacity: 1 = opaque, less is see-through
# emission: glow in its own color (0 = none)
MATERIALS = {
    "ecal_tower": ((0.01, 1.0, 0.01, 1.0), 0.5, 0.5),
    "hcal_tower": ((0.033, 0.448, 1.0, 1.0), 0.5, 0.5),
    "jet": ((1.0, 0.214, 0.0, 1.0), 0.3, 0.0),
}

# Solids: name prefix -> material name
SOLIDS = {
    "EcalTowers_V": "ecal_tower",
    "HcalTowers_V": "hcal_tower",
    "PATJets_V": "jet",
}

MARK = "principled"   # custom property on materials that should stay lit

FLAT_NODES = {'EMISSION', 'BACKGROUND', 'BSDF_TRANSPARENT', 'LIGHT_PATH', 'MIX_SHADER'}


def principled_material(name, color, alpha, emission):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Alpha"].default_value = alpha
    bsdf.inputs["Emission Color"].default_value = color
    bsdf.inputs["Emission Strength"].default_value = emission
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mat.diffuse_color = (*color[:3], alpha)
    mat.surface_render_method = 'BLENDED' if alpha < 1.0 else 'DITHERED'
    mat[MARK] = True
    return mat


def is_lit(nt):
    return any(n.type.startswith('BSDF_') and n.type != 'BSDF_TRANSPARENT'
               for n in nt.nodes)


def linked_from(socket, node_type):
    return socket.is_linked and socket.links[0].from_node.type == node_type


def transfer(nt, src, dst):
    # Copy a socket's value, or re-route whatever is plugged into it
    if src.is_linked:
        nt.links.new(src.links[0].from_socket, dst)
    else:
        dst.default_value = src.default_value


def to_principled(mat):
    nt = mat.node_tree
    if nt is None:
        return False
    if is_lit(nt):
        mat[MARK] = True
        return False

    out = nt.get_output_node('ALL') or nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = out.location.x - 300, out.location.y

    # Color: from the Emission/Background node, else the viewport color
    emit = next((n for n in nt.nodes if n.type in {'EMISSION', 'BACKGROUND'}), None)
    if emit is not None:
        transfer(nt, emit.inputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = mat.diffuse_color

    # Alpha: the Fac of a "Transparent / color" mix that isn't the
    # glTF Light Path trick
    alpha_mix = next((n for n in nt.nodes if n.type == 'MIX_SHADER'
                      and linked_from(n.inputs[1], 'BSDF_TRANSPARENT')
                      and not linked_from(n.inputs[0], 'LIGHT_PATH')), None)
    if alpha_mix is not None:
        transfer(nt, alpha_mix.inputs[0], bsdf.inputs["Alpha"])

    for n in [n for n in nt.nodes if n.type in FLAT_NODES]:
        nt.nodes.remove(n)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    alpha = bsdf.inputs["Alpha"]
    if alpha.is_linked or alpha.default_value < 1.0:
        mat.surface_render_method = 'BLENDED'
    mat[MARK] = True
    return True


for name, (color, opacity, emission) in MATERIALS.items():
    principled_material(name, color, opacity, emission)

for prefix, mat_name in SOLIDS.items():
    objs = [o for o in bpy.data.objects if o.name.startswith(prefix)
            and o.type == 'MESH' and len(o.data.polygons) > 0]
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(bpy.data.materials[mat_name])
    print(f"{prefix}: set {mat_name} on {len(objs)} objects")

materials = {s.material for o in bpy.context.scene.objects
             for s in o.material_slots if s.material}

converted = [m.name for m in materials if to_principled(m)]
print(f"Converted {len(converted)} of {len(materials)} materials to Principled BSDF")
for name in sorted(converted):
    print("  " + name)
