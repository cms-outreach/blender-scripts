# <thomas.mccauley@cern.ch>

import bpy

def convert_to_curves(name, material):

    for o in bpy.data.objects[name].children:

        # Select object and make it active
        o.select_set(True)
        bpy.context.view_layer.objects.active = o

        # Convert to a curve
        bpy.ops.object.convert(target='CURVE')

        # Set curve properties
        bpy.context.object.data.bevel_depth = 0.01
        bpy.context.object.data.bevel_resolution = 24
        bpy.context.object.data.use_fill_caps = True

        # Link material to the object
        bpy.context.active_object.data.materials.append(material)

        
collections = [
    "GlobalMuons_V1",
    "Tracks_V3",
    "GsfElectrons_V2"
]

muon_mat = bpy.data.materials.new(name="muon")
muon_mat.use_nodes = True
bpy.data.materials["muon"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (1.0, 0.0, 0.0, 1)

track_mat = bpy.data.materials.new(name="track")
track_mat.use_nodes = True
bpy.data.materials["track"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (1.0, 1.0, 0.0, 1)

electron_mat = bpy.data.materials.new(name="electron")
electron_mat.use_nodes = True
bpy.data.materials["electron"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.1, 1.0, 0.1, 1)

convert_to_curves(collections[0], muon_mat)
convert_to_curves(collections[1], track_mat)
convert_to_curves(collections[2], electron_mat)





    
