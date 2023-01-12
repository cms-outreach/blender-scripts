# <thomas.mccauley@cern.ch>

import bpy

world = bpy.data.worlds["World"]

# This color is 0x202020 in hex
r = 0.014
g = 0.014
b = 0.014
a = 1

bg_color = (r, g, b, a)

world.node_tree.nodes["Background"].inputs[0].default_value = bg_color
