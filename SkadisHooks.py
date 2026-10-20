"""Skadis Hooks - Fusion 360 add-in.

Adds IKEA SKADIS pegboard hooks to a selected planar face. Each hook is an
L-shaped peg: an arm that sticks straight out of the face (through the board)
and a leg that drops down behind the board. Hooks are laid out on the SKADIS
slot grid (40 mm horizontal pitch, staggered rows).

All Fusion API lengths are in centimetres; inputs are shown in mm.
"""

import adsk.core
import adsk.fusion
import os
import traceback

CMD_ID = 'jman_SkadisHooks'
CMD_NAME = 'Skadis Hooks'
CMD_TOOLTIP = 'Add IKEA SKADIS pegboard hooks to a planar face.'
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'
RESOURCES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')

UP_CHOICES = ['Auto', '+Z', '-Z', '+Y', '-Y', '+X', '-X']
UP_VECTORS = {
    '+X': (1, 0, 0), '-X': (-1, 0, 0),
    '+Y': (0, 1, 0), '-Y': (0, -1, 0),
    '+Z': (0, 0, 1), '-Z': (0, 0, -1),
}
OP_JOIN = 'Join'
OP_NEW = 'New Body'

# Defaults (lengths in cm). Remembered for the rest of the Fusion session.
_settings = {
    'cols': 2,
    'rows': 2,
    'staggered': True,
    'operation': OP_JOIN,
    'up': 'Auto',
    'offsetX': 0.0,
    'offsetY': 0.0,
    'hookWidth': 0.45,     # 4.5 mm  - side-to-side, fits the 5 mm slot
    'hookDepth': 0.53,     # 5.3 mm  - arm length = gap for the 5 mm board
    'armHeight': 0.5,      # 5 mm    - vertical thickness of the arm
    'legThickness': 0.45,  # 4.5 mm  - leg thickness behind the board
    'totalHeight': 1.2,    # 12 mm   - top of arm to bottom of leg (< 15 mm slot)
    'roundLeg': True,
    'hPitch': 4.0,         # 40 mm   - hook-to-hook in a row
    'vPitch': 4.0,         # 40 mm   - same column, row to row (staggered rows sit halfway)
}

_app = None
_ui = None
_handlers = []


def run(context):
    global _app, _ui
    try:
        _app = adsk.core.Application.get()
        _ui = _app.userInterface

        cmd_def = _ui.commandDefinitions.itemById(CMD_ID)
        if cmd_def:
            cmd_def.deleteMe()
        cmd_def = _ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_TOOLTIP, RESOURCES)

        on_created = CommandCreatedHandler()
        cmd_def.commandCreated.add(on_created)
        _handlers.append(on_created)

        panel = _ui.workspaces.itemById(WORKSPACE_ID).toolbarPanels.itemById(PANEL_ID)
        ctrl = panel.controls.itemById(CMD_ID)
        if ctrl:
            ctrl.deleteMe()
        panel.controls.addCommand(cmd_def)
    except:
        if _ui:
            _ui.messageBox('Skadis Hooks failed to start:\n{}'.format(traceback.format_exc()))


def stop(context):
    try:
        panel = _ui.workspaces.itemById(WORKSPACE_ID).toolbarPanels.itemById(PANEL_ID)
        ctrl = panel.controls.itemById(CMD_ID)
        if ctrl:
            ctrl.deleteMe()
        cmd_def = _ui.commandDefinitions.itemById(CMD_ID)
        if cmd_def:
            cmd_def.deleteMe()
    except:
        if _ui:
            _ui.messageBox('Skadis Hooks failed to stop:\n{}'.format(traceback.format_exc()))


# ---------------------------------------------------------------------------
# Command UI
# ---------------------------------------------------------------------------

class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs
            s = _settings

            sel = inputs.addSelectionInput('face', 'Face', 'Select a planar face to put hooks on')
            sel.addSelectionFilter('PlanarFaces')
            sel.setSelectionLimits(1, 1)

            inputs.addIntegerSpinnerCommandInput('cols', 'Width (hooks)', 1, 100, 1, s['cols'])
            inputs.addIntegerSpinnerCommandInput('rows', 'Height (rows)', 1, 100, 1, s['rows'])
            inputs.addBoolValueInput('staggered', 'Staggered rows', True, '', s['staggered'])

            op = inputs.addDropDownCommandInput('operation', 'Operation', adsk.core.DropDownStyles.TextListDropDownStyle)
            for name in (OP_JOIN, OP_NEW):
                op.listItems.add(name, name == s['operation'])

            up = inputs.addDropDownCommandInput('up', 'Up direction', adsk.core.DropDownStyles.TextListDropDownStyle)
            for name in UP_CHOICES:
                up.listItems.add(name, name == s['up'])

            _value(inputs, 'offsetX', 'Offset horizontal', s['offsetX'])
            _value(inputs, 'offsetY', 'Offset vertical', s['offsetY'])

            dims = inputs.addGroupCommandInput('dims', 'Hook dimensions')
            dims.isExpanded = False
            d = dims.children
            _value(d, 'hookWidth', 'Width', s['hookWidth'])
            _value(d, 'hookDepth', 'Depth (gap)', s['hookDepth'])
            _value(d, 'armHeight', 'Arm height', s['armHeight'])
            _value(d, 'legThickness', 'Leg thickness', s['legThickness'])
            _value(d, 'totalHeight', 'Total height', s['totalHeight'])
            d.addBoolValueInput('roundLeg', 'Rounded leg', True, '', s['roundLeg'])

            spacing = inputs.addGroupCommandInput('spacing', 'Spacing')
            spacing.isExpanded = False
            _value(spacing.children, 'hPitch', 'Horizontal pitch', s['hPitch'])
            _value(spacing.children, 'vPitch', 'Vertical pitch', s['vPitch'])

            for event, handler in (
                (cmd.execute, ExecuteHandler()),
                (cmd.executePreview, PreviewHandler()),
                (cmd.validateInputs, ValidateHandler()),
            ):
                event.add(handler)
                _handlers.append(handler)
        except:
            _ui.messageBox('Skadis Hooks:\n{}'.format(traceback.format_exc()))


def _value(inputs, input_id, name, cm):
    return inputs.addValueInput(input_id, name, 'mm', adsk.core.ValueInput.createByReal(cm))


def _read(inputs):
    p = {}
    for key in ('cols', 'rows'):
        p[key] = inputs.itemById(key).value
    for key in ('staggered', 'roundLeg'):
        p[key] = inputs.itemById(key).value
    for key in ('operation', 'up'):
        p[key] = inputs.itemById(key).selectedItem.name
    for key in ('offsetX', 'offsetY', 'hookWidth', 'hookDepth', 'armHeight',
                'legThickness', 'totalHeight', 'hPitch', 'vPitch'):
        p[key] = inputs.itemById(key).value
    return p


def _problem(p):
    """Return a reason the parameters can't build, or None."""
    for key in ('hookWidth', 'hookDepth', 'armHeight', 'legThickness', 'totalHeight', 'hPitch', 'vPitch'):
        if p[key] <= 0:
            return 'All dimensions must be positive.'
    if p['totalHeight'] <= p['armHeight']:
        return 'Total height must be greater than arm height.'
    if p['roundLeg'] and p['legThickness'] <= p['hookWidth'] / 2 + 1e-4:
        return 'Rounded leg needs leg thickness greater than half the hook width.'
    return None


class ValidateHandler(adsk.core.ValidateInputsEventHandler):
    def notify(self, args):
        try:
            args.areInputsValid = _problem(_read(args.inputs)) is None
        except:
            args.areInputsValid = False


class PreviewHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            build(args.command.commandInputs)
            args.isValidResult = True
        except:
            # Leave the preview empty; execute will report the actual error.
            args.isValidResult = False


class ExecuteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            build(args.command.commandInputs)
        except Exception as e:
            args.executeFailed = True
            args.executeFailedMessage = str(e)
            _ui.messageBox('Skadis Hooks failed:\n{}'.format(traceback.format_exc()))


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

def build(inputs):
    p = _read(inputs)
    _settings.update(p)
    problem = _problem(p)
    if problem:
        raise ValueError(problem)

    sel = inputs.itemById('face')
    if sel.selectionCount != 1:
        raise ValueError('Select a planar face.')
    face = adsk.fusion.BRepFace.cast(sel.selection(0).entity)
    # Work in the face's own component so it also works on faces of occurrences.
    face = face.nativeObject or face
    target = face.body
    comp = target.parentComponent
    design = adsk.fusion.Design.cast(comp.parentDesign)

    ok, normal = face.evaluator.getNormalAtPoint(face.pointOnFace)
    if not ok:
        raise ValueError('Could not evaluate the face normal.')
    normal.normalize()
    up = _up_vector(normal, p['up'])
    if up is None:
        raise ValueError('Up direction {} is perpendicular to the face; pick another.'.format(p['up']))
    right = up.crossProduct(normal)
    right.normalize()
    centre = face.centroid

    def point(x, y, z):
        return adsk.core.Point3D.create(
            centre.x + right.x * x + up.x * y + normal.x * z,
            centre.y + right.y * x + up.y * y + normal.y * z,
            centre.z + right.z * x + up.z * y + normal.z * z,
        )

    tbm = adsk.fusion.TemporaryBRepManager.get()
    hooks = [_make_hook(tbm, point, right, up, x, y, p) for x, y in _layout(p)]

    if design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
        base = comp.features.baseFeatures.add()
        base.startEdit()
        for h in hooks:
            comp.bRepBodies.add(h, base)
        base.finishEdit()
        base.name = 'Skadis Hooks'
        bodies = [base.bodies.item(i) for i in range(base.bodies.count)]
    else:
        bodies = [comp.bRepBodies.add(h) for h in hooks]

    for i, b in enumerate(bodies):
        b.name = 'Skadis Hook {}'.format(i + 1)

    if p['operation'] == OP_JOIN:
        tools = adsk.core.ObjectCollection.create()
        for b in bodies:
            tools.add(b)
        combine = comp.features.combineFeatures.createInput(target, tools)
        combine.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        combine.isKeepToolBodies = False
        comp.features.combineFeatures.add(combine)


def _up_vector(normal, choice):
    """Project the chosen world axis onto the face plane."""
    if choice == 'Auto':
        candidates, min_len = ['+Z', '+Y', '+X'], 0.3
    else:
        candidates, min_len = [choice], 1e-3
    for key in candidates:
        a = adsk.core.Vector3D.create(*UP_VECTORS[key])
        d = a.dotProduct(normal)
        v = adsk.core.Vector3D.create(a.x - d * normal.x, a.y - d * normal.y, a.z - d * normal.z)
        if v.length > min_len:
            v.normalize()
            return v
    return None


def _layout(p):
    """Hook positions (x, y) on the face, y = top of the hook, centred on the face."""
    cols, rows, hp, vp = p['cols'], p['rows'], p['hPitch'], p['vPitch']
    pts = []
    for r in range(rows):
        if p['staggered']:
            y = -r * vp / 2
            if r % 2 == 0:
                xs = [c * hp for c in range(cols)]
            elif cols > 1:
                xs = [(c + 0.5) * hp for c in range(cols - 1)]
            else:
                xs = [hp / 2]
        else:
            y = -r * vp
            xs = [c * hp for c in range(cols)]
        pts.extend((x, y) for x in xs)

    xs = [x for x, _ in pts]
    ys = [y for _, y in pts]
    cx = (min(xs) + max(xs)) / 2
    cy = (max(ys) + min(ys) - p['totalHeight']) / 2
    return [(x - cx + p['offsetX'], y - cy + p['offsetY']) for x, y in pts]


def _make_hook(tbm, point, right, up, x, y, p):
    """One L-shaped hook whose arm top-centre sits at (x, y) on the face.

    Local axes: right (hook width), up, normal (out of the face).
      arm: out of the face from 0 to the leg, armHeight tall
      leg: starts hookDepth out, drops to totalHeight, outer side rounded
    """
    w = p['hookWidth']
    depth = p['hookDepth']
    leg_t = p['legThickness']
    h = p['totalHeight']
    r = w / 2 if p['roundLeg'] else 0.0
    leg_box = leg_t - r
    reach = depth + leg_box  # how far the square part of the hook sticks out

    def box(cz, ly, lz, cy):
        obb = adsk.core.OrientedBoundingBox3D.create(point(x, y + cy, cz), right, up, w, ly, lz)
        return tbm.createBox(obb)

    hook = box(reach / 2, p['armHeight'], reach, -p['armHeight'] / 2)
    leg = box(depth + leg_box / 2, h, leg_box, -h / 2)
    tbm.booleanOperation(hook, leg, adsk.fusion.BooleanTypes.UnionBooleanType)
    if r > 0:
        cyl = tbm.createCylinderOrCone(point(x, y - h, reach), r, point(x, y, reach), r)
        tbm.booleanOperation(hook, cyl, adsk.fusion.BooleanTypes.UnionBooleanType)
    return hook
