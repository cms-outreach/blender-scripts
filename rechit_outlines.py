import bpy
from collections import defaultdict

# White flat-coloured lines along the edges of the ECAL and HCAL rec hits,
# like ecal_tower_outlines.py and hcal_tower_outlines.py do for towers.
# Objects are matched by name prefix without the version number.
# Safe to run more than once.
# ---- Settings (scene units are metres) ----
LINE_COLOR = (1.0, 1.0, 1.0, 1.0)   # white
RESOLUTION = 6

# name prefix -> line thickness (tube radius)
PREFIXES = {
    "EBRecHits_V": 0.001,    # ECAL barrel
    "EERecHits_V": 0.001,    # ECAL endcap
    "ESRecHits_V": 0.001,    # preshower
    "HBRecHits_V": 0.0015,   # HCAL barrel
    "HERecHits_V": 0.0015,   # HCAL endcap
    "HFRecHits_V": 0.0015,   # HCAL forward
    "HORecHits_V": 0.0015,   # HCAL outer
}

NAME = "RecHits_Outline"

# ---- Flat white material ----
mat = bpy.data.materials.get(NAME) or bpy.data.materials.new(NAME)
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
em = nt.nodes.new("ShaderNodeEmission")
em.inputs["Color"].default_value = LINE_COLOR
em.inputs["Strength"].default_value = 1.0
out = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(em.outputs["Emission"], out.inputs["Surface"])


def tube_group(name, radius):
    """Geometry Nodes: edges -> thin tubes"""
    old = bpy.data.node_groups.get(name)
    if old is not None:
        bpy.data.node_groups.remove(old)
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n, link = ng.nodes, ng.links.new
    gin, gout = n.new("NodeGroupInput"), n.new("NodeGroupOutput")
    m2c = n.new("GeometryNodeMeshToCurve")
    prof = n.new("GeometryNodeCurvePrimitiveCircle")
    prof.inputs["Resolution"].default_value = RESOLUTION
    prof.inputs["Radius"].default_value = radius
    c2m = n.new("GeometryNodeCurveToMesh")
    setm = n.new("GeometryNodeSetMaterial")
    setm.inputs["Material"].default_value = mat
    link(gin.outputs[0], m2c.inputs["Mesh"])
    link(m2c.outputs["Curve"], c2m.inputs["Curve"])
    link(prof.outputs["Curve"], c2m.inputs["Profile Curve"])
    link(c2m.outputs["Mesh"], setm.inputs["Geometry"])
    link(setm.outputs["Geometry"], gout.inputs[0])
    return ng


def outline_edges(mesh):
    """Box edges only: drop the diagonals between coplanar triangles of the same face.
    Edges shared by neighbouring hits are drawn once."""
    key = lambda co: (round(co.x, 6), round(co.y, 6), round(co.z, 6))
    normals = defaultdict(list)
    for poly in mesh.polygons:
        if poly.area == 0:
            continue
        vs = [key(mesh.vertices[i].co) for i in poly.vertices]
        for a, b in zip(vs, vs[1:] + vs[:1]):
            if a != b:
                normals[frozenset((a, b))].append(poly.normal.copy())
    return [tuple(e) for e, ns in normals.items()
            if len(ns) < 2 or any(abs(ns[i].dot(ns[k])) < 0.9999
                                  for i in range(len(ns)) for k in range(i + 1, len(ns)))]


for prefix, radius in PREFIXES.items():
    sources = [o for o in bpy.data.objects
               if o.type == 'MESH' and o.name.startswith(prefix)
               and not o.name.endswith("_outline") and len(o.data.polygons) > 0]
    if not sources:
        continue
    ng = tube_group(prefix + "_OutlineTubes", radius)

    for src in sources:
        old = bpy.data.objects.get(src.name + "_outline")
        if old is not None:
            bpy.data.objects.remove(old, do_unlink=True)

        edges = outline_edges(src.data)
        verts, index, edge_idx = [], {}, []
        for a, b in edges:
            for v in (a, b):
                if v not in index:
                    index[v] = len(verts)
                    verts.append(v)
            edge_idx.append((index[a], index[b]))

        me = bpy.data.meshes.new(src.name + "_outline")
        me.from_pydata(verts, edge_idx, [])
        ob = bpy.data.objects.new(src.name + "_outline", me)
        for col in src.users_collection:
            col.objects.link(ob)
        ob.parent = src.parent
        ob.matrix_parent_inverse = src.matrix_parent_inverse.copy()
        ob.matrix_basis = src.matrix_basis.copy()
        ob.modifiers.new("OutlineStyle", 'NODES').node_group = ng
        print(f"{src.name}: {len(edge_idx)} outline edges")
