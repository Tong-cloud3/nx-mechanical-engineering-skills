# -*- coding: utf-8 -*-
"""Shared helpers for operation sketches."""
from sheetgen import Sheet, tbl


def notes(s, lines, y=54.0, x=24.0, step=5.2, h=3.0):
    s.set_view(1, 0, 0)
    for txt, layer in lines:
        s.RT(x, y, h, txt, 0, layer)
        y -= step


def band(s, x1, y1, x2, y2, gap=5.0):
    s.FILLR(x1, y1, x2, y2)
    s.HATCH(x1, y1, x2, y2, gap)


def chuck(s, x, y1, y2, label_y=None, label_dx=0.0):
    """Three-jaw chuck symbol on the left of a turned part (sheet coords)."""
    s.set_view(1, 0, 0)
    s.L(x, y1, x, y2, 'FIXTURE')
    for yy in (y1, (y1 + y2) / 2.0, y2):
        s.L(x, yy, x + 6, yy, 'FIXTURE')
        s.L(x - 10, yy, x, yy, 'FIXTURE')
    s.L(x - 10, y1, x - 10, y2, 'FIXTURE')
    s.RT(x - 5 + label_dx, (y2 + 4.0) if label_y is None else label_y, 2.8, '三爪自定心', 1, 'FIXTURE')


def mill(s, x, part_top, label, r=8.0):
    """Face mill / end mill from above; label to the right of the cutter."""
    s.set_view(1, 0, 0)
    cy = part_top + 14 + r
    s.C(x, cy, r, 'TOOL')
    s.C(x, cy, 1.6, 'TOOL')
    s._line((x, cy - r), (x, part_top + 1), 'TOOL')
    s._arrowhead((x, part_top + 1), (x, part_top + 8), 1.9, 'TOOL')
    s.RT(x + r + 2, cy, 3.1, label, 0, 'TOOL')
    return cy


def drill(s, x, part_top, label, r=3.0, label_dy=None):
    """Drill from above: small circle + crosshair + arrow; label to the right."""
    s.set_view(1, 0, 0)
    cy = part_top + 12 + r
    s.C(x, cy, r, 'TOOL')
    s._line((x - r - 1, cy), (x + r + 1, cy), 'TOOL')
    s._line((x, cy - r - 1), (x, cy + r + 1), 'TOOL')
    s._line((x, cy - r), (x, part_top + 1), 'TOOL')
    s._arrowhead((x, part_top + 1), (x, part_top + 7), 1.8, 'TOOL')
    s.RT(x + r + 3, cy if label_dy is None else cy + label_dy, 3.0, label, 0, 'TOOL')
    return cy


def bar(s, x_tip, y, label):
    """Boring bar entering from the right at height y (sheet coords)."""
    s.set_view(1, 0, 0)
    x2 = x_tip + 30
    s._line((x_tip, y), (x2, y), 'TOOL')
    s._rect_raw(x2, y - 3.2, x2 + 26, y + 3.2, 'TOOL')
    s._arrowhead((x_tip, y), (x_tip + 10, y), 1.9, 'TOOL')
    s.RT(x2 + 30, y, 3.0, label, 0, 'TOOL')


def carriage(s, x_tip, y, label):
    """Turning tool on a post approaching from above (sheet coords)."""
    s.set_view(1, 0, 0)
    top = y + 16
    s._line((x_tip, top), (x_tip, y + 1.2), 'TOOL')
    s._arrowhead((x_tip, y + 1.2), (x_tip, y + 7), 1.8, 'TOOL')
    s._rect_raw(x_tip - 2.4, top, x_tip + 2.4, top + 8, 'TOOL')
    s.RT(x_tip + 4, top + 2, 3.0, label, 0, 'TOOL')


def sup_at(s, cx, cy, r, ang_deg):
    """Fixed locating support on a circular outline (angle in degrees)."""
    import math
    a = math.radians(ang_deg)
    x, y = cx + r * math.cos(a), cy + r * math.sin(a)
    dx, dy = -math.cos(a), -math.sin(a)
    if abs(dy) >= abs(dx):
        d = 0 if dy > 0 else 3
    else:
        d = 1 if dx > 0 else 2
    s.SUP(x, y, 0, d)
