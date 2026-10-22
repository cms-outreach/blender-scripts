# blender-scripts
Useful scripts for rendering CMS event displays exported from iSpy WebGL
(`.gltf` / `.glb`) with the [Blender Python API](https://docs.blender.org/api/current/index.html).

Requires **Blender 5.x** (tested with Blender 5.2.2). EEVEE is the recommended
render engine.

## Scripts

### Event objects

* `fix_objects.py`

Draws tracks, muons, electrons, photons, and the MET arrow as tubes so that they
are visible when rendered. Photons are dashed. Tubes keep the flat (unlit)
colors from the glb file until `principled_materials.py` is run.

* `principled_materials.py`

Converts the flat materials in the scene to lit Principled BSDF materials, so
that objects respond to lights and shading. ECAL and HCAL towers and jets get
their own materials; the towers glow slightly.

* `rechit_outlines.py`

Adds white outlines along the edges of the ECAL and HCAL rec hits.

* `ecal_tower_outlines.py`, `hcal_tower_outlines.py`

Add white outlines along the edges of the ECAL and HCAL towers.

### Detector geometry

* `fix_geometry.py`

Makes imported detector geometry (such as `muon-2.glb`) opaque and non-metallic,
so that it renders cleanly with lights. Set the root object names in `ROOTS`.

### Lighting and look

* `clean_scene.py`

Removes the lights that come with the iSpy WebGL export and Blender's default
cube and light.

* `add_lights.py`

Adds three-point lighting (key, fill, and rim Sun lights) placed relative to the
active camera. Run it again after moving the camera.

* `render_look.py`

Makes renders crisp and saturated: uses the Standard view transform and makes
the detector more transparent so it doesn't look hazy.

* `change_background.py`

Changes the background color (to `0x202020`).

* `bloom.py`

Adds a glow (bloom) to photons, electrons, muons, and jets using the compositor.
To see it in the viewport, use Rendered shading with
Viewport Shading > Compositor set to Always.

## Usage

* Open Blender

* Import a `.gltf` or `.glb` file exported from iSpy WebGL

* Select "Scripting" from the main menu

* Select "Open Text" and select a python script

* Then run using the "Run Script" button (or the "Alt P" shortcut)

Each script can be run on its own and is safe to run more than once. For a full
event display, a suggested order is:

1. `clean_scene.py`
2. `change_background.py`
3. `fix_objects.py`
4. `principled_materials.py`
5. `rechit_outlines.py`, `ecal_tower_outlines.py`, `hcal_tower_outlines.py`
6. `fix_geometry.py` (only for detector geometry files)
7. `add_lights.py`
8. `render_look.py`
9. `bloom.py` (last, since `fix_objects.py` and `principled_materials.py`
   rebuild materials)
