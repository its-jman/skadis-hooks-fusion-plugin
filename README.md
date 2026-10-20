# Skadis Hooks for Fusion 360

A Fusion 360 add-in that adds IKEA SKÅDIS pegboard hooks to a planar face.

Select a face, choose how many hooks across (width) and how many rows down (height), and the add-in places L-shaped hooks on the SKÅDIS slot grid: 40 mm apart, with staggered rows offset by 20 mm.

## Install

1. Clone this repo into Fusion's add-ins folder (or symlink it there as `SkadisHooks`):
   - macOS: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/SkadisHooks`
   - Windows: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\SkadisHooks`
2. In Fusion, open **Utilities → Add-Ins → Scripts and Add-Ins** (Shift+S).
3. Turn on the **Run** toggle for **SkadisHooks**. Turn on **Run on Startup** to load it every time.

## Use

**Solid → Create → Skadis Hooks**

| Option | Default | Notes |
| --- | --- | --- |
| Face | — | The face that rests against the board |
| Width (hooks) | 2 | Hooks per row |
| Height (rows) | 2 | Staggered rows have one fewer hook, centred between |
| Staggered rows | on | Off places rows straight down at the vertical pitch |
| Operation | Join | Join to the face's body, or create new bodies |
| Up direction | Auto | Which way is up on the face (+Z, then +Y) |
| Offset horizontal / vertical | 0 mm | Shift the hook grid from the face centre |

**Hook dimensions:** width 4.5 mm, depth (gap for the board) 5.3 mm, arm height 5 mm, leg thickness 4.5 mm, total height 12 mm, rounded leg.

**Spacing:** horizontal pitch 40 mm, vertical pitch 40 mm.
