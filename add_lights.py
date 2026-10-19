import bpy
from mathutils import Vector

# Add three-point lighting (key, fill, rim) using Sun lights, so it works
# at any scene scale. Directions are relative to the active camera if
# there is one, otherwise to the front (-Y) view.
# Safe to run more than once: the lights are updated, not duplicated.

COLLECTION = "Lights"

# name: (direction toward the light in camera space (right, up, back),
#        strength, angle in degrees (softness of shadows))
LIGHTS = {
    "Key":  ((-1.0, 1.0, 1.0), 3.0, 10.0),   # upper left, in front
    "Fill": ((1.0, 0.2, 1.0), 1.0, 30.0),    # right, in front, soft
    "Rim":  ((0.3, 1.0, -1.0), 2.0, 5.0),    # above, behind
}


def view_axes():
    cam = bpy.context.scene.camera
    if cam is not None:
        m = cam.matrix_world.to_3x3().normalized()
        return m.col[0], m.col[1], m.col[2]   # right, up, back (toward camera)
    return Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0))


def scene_center():
    pts = [o.matrix_world @ Vector(c) for o in bpy.context.scene.objects
           if o.type in {'MESH', 'CURVE'} for c in o.bound_box]
    if not pts:
        return Vector((0, 0, 0)), 1.0
    lo = Vector(tuple(min(p[i] for p in pts) for i in range(3)))
    hi = Vector(tuple(max(p[i] for p in pts) for i in range(3)))
    return (lo + hi) / 2, max((hi - lo).length, 1.0)


coll = bpy.data.collections.get(COLLECTION)
if coll is None:
    coll = bpy.data.collections.new(COLLECTION)
    bpy.context.scene.collection.children.link(coll)

# Make sure camera and object matrices are up to date
bpy.context.view_layer.update()

right, up, back = view_axes()
center, size = scene_center()

for name, ((x, y, z), strength, angle) in LIGHTS.items():
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != 'LIGHT':
        obj = bpy.data.objects.new(name, bpy.data.lights.new(name, 'SUN'))
        coll.objects.link(obj)
    light = obj.data
    light.type = 'SUN'
    light.energy = strength
    light.angle = angle * 3.14159265 / 180

    # A sun shines along its local -Z, so point -Z away from the light's side
    direction = (right * x + up * y + back * z).normalized()
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = (-direction).to_track_quat('-Z', 'Y')
    # Position only matters for seeing it in the viewport
    obj.location = center + direction * size * 0.75

print(f"Added lights to '{COLLECTION}': {', '.join(LIGHTS)}")
