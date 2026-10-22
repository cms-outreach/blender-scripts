import bpy
from collections import defaultdict

# White flat-coloured lines along the edges of the ECAL towers.
# ---- Settings (scene units are metres) ----
PREFIX = "EcalTowers_V1"
LINE_COLOR = (1.0, 1.0, 1.0, 1.0)   # white
RADIUS = 0.001                    # line thickness (tube radius)
RESOLUTION = 6

NAME = PREFIX + "_Outline"

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

# ---- Geometry Nodes: edges -> thin tubes ----
old = bpy.data.node_groups.get(NAME + "Tubes")
if old is not None:
    bpy.data.node_groups.remove(old)
ng = bpy.data.node_groups.new(NAME + "Tubes", "GeometryNodeTree")
ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
n, link = ng.nodes, ng.links.new
gin, gout = n.new("NodeGroupInput"), n.new("NodeGroupOutput")
m2c = n.new("GeometryNodeMeshToCurve")
prof = n.new("GeometryNodeCurvePrimitiveCircle")
prof.inputs["Resolution"].default_value = RESOLUTION
prof.inputs["Radius"].default_value = RADIUS
c2m = n.new("GeometryNodeCurveToMesh")
setm = n.new("GeometryNodeSetMaterial")
setm.inputs["Material"].default_value = mat
link(gin.outputs[0], m2c.inputs["Mesh"])
link(m2c.outputs["Curve"], c2m.inputs["Curve"])
link(prof.outputs["Curve"], c2m.inputs["Profile Curve"])
link(c2m.outputs["Mesh"], setm.inputs["Geometry"])
link(setm.outputs["Geometry"], gout.inputs[0])


def outline_edges(mesh):
    """Box edges only: drop the diagonals between coplanar triangles of the same face.
    Edges shared by neighbouring towers are drawn once."""
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


for src in [o for o in bpy.data.objects
            if o.type == 'MESH' and o.name.startswith(PREFIX)
            and not o.name.endswith("_outline") and len(o.data.polygons) > 0]:
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
