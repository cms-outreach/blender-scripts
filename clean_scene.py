import bpy

# Remove the lights that come with an iSpy WebGL export (the "Lights" empty
# and its Sun lights, Light1 and Light2) and Blender's default cube and
# light.
# Lights added by add_lights.py are left alone.
# Safe to run more than once.

LIGHTS_ROOT = "Lights"   # iSpy's empty holding its lights
CUBE = "Cube"
LIGHT = "Light"          # Blender's default point light


def remove(obj):
    data = obj.data
    bpy.data.objects.remove(obj)
    if data is not None and data.users == 0:
        if isinstance(data, bpy.types.Light):
            bpy.data.lights.remove(data)
        elif isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)


# iSpy lights ("Lights", or "Lights.001" etc. if imported more than once)
roots = [o for o in bpy.data.objects if o.type == 'EMPTY'
         and o.name.split(".")[0] == LIGHTS_ROOT]
lights = [c for r in roots for c in r.children_recursive if c.type == 'LIGHT']
for o in lights + roots:
    remove(o)
print(f"Removed {len(lights)} iSpy lights")

cube = bpy.data.objects.get(CUBE)
if cube is not None and cube.type == 'MESH':
    remove(cube)
    print("Removed the default cube")

light = bpy.data.objects.get(LIGHT)
if light is not None and light.type == 'LIGHT':
    remove(light)
    print("Removed the default light")
