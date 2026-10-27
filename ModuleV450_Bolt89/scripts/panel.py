#!/usr/bin/env python3
"""Customer panel ("Panel by Customer") for JLCPCB SMT assembly.
N copies of a board (any outline with straight long edges) stacked vertically, 2 mm milled gaps, 5 mm tabs with mouse-bite holes,
5 mm rails top/bottom with 3 fiducials and 3 tooling holes (1.152 mm, JLC standard).
usage: panel.py board.kicad_pcb out.kicad_pcb N [tab_x,tab_x,...] [name]
References stay as on the single board (silkscreen unchanged); jlc.py numbers the copies _1.._N from top to bottom."""
import sys, math
import pcbnew
from pcbnew import VECTOR2I, FromMM as MM, ToMM
from shapely.geometry import box, Polygon
from shapely.affinity import translate
from shapely.ops import unary_union

src_file, out_file, N = sys.argv[1], sys.argv[2], int(sys.argv[3])
GAP, RAIL, TABW = 2.0, 5.0, 5.0
TABS_X = [float(v) for v in sys.argv[4].split(',')] if len(sys.argv) > 4 else [0.0, 62.0, 100.0]   # board-local x of tabs
NAME = sys.argv[5] if len(sys.argv) > 5 else 'ModuleV450_Bolt89'
KEEP_DEPTH = 0.7                     # copper keep-out into the board at each tab
OX, OY = 60.0, 100.0                 # board-local origin used by the generator

b = pcbnew.LoadBoard(src_file)
# board outline (local)
bb = b.GetBoardEdgesBoundingBox()
x0, y0 = ToMM(bb.GetX()) - OX, ToMM(bb.GetY()) - OY
w, h = ToMM(bb.GetWidth()), ToMM(bb.GetHeight())
lw = 0.1
x0 += lw / 2; y0 += lw / 2; w -= lw; h -= lw          # line-width correction -> true edge
x1, y1 = x0 + w, y0 + h
print('board %.2f x %.2f mm' % (w, h))
# real board shape (round ends etc.)
_sps = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(_sps)
_o = _sps.Outline(0)
BRD = Polygon([(ToMM(_o.CPoint(i).x) - OX, ToMM(_o.CPoint(i).y) - OY) for i in range(_o.PointCount())])

# clip every zone to its own board, otherwise the oversized pours (BIG) spill onto the neighbour board / rails
from shapely.geometry import Polygon
brd = BRD
for z in list(b.Zones()):
    o = z.Outline().Outline(0)
    poly = Polygon([(ToMM(o.CPoint(i).x) - OX, ToMM(o.CPoint(i).y) - OY) for i in range(o.PointCount())]).intersection(brd)
    if poly.is_empty:
        b.Remove(z); continue
    if poly.geom_type != 'Polygon':
        poly = max(poly.geoms, key=lambda g: g.area)
    ol = z.Outline(); ol.RemoveAllContours(); ol.NewOutline()
    for (x, y) in list(poly.exterior.coords)[:-1]:
        ol.Append(MM(OX + x), MM(OY + y))
FPS = list(b.GetFootprints())
DRAW = list(b.GetDrawings())
items = FPS + list(b.GetTracks()) + list(b.Zones())
# remove original outline
for d in DRAW:
    if d.GetLayer() == pcbnew.Edge_Cuts:
        b.Remove(d)
    else:
        items.append(d)

PITCH_Y = h + GAP
for k in range(1, N):
    dy = MM(k * PITCH_Y)
    for it in items:
        c = it.Duplicate()
        c.Move(VECTOR2I(0, dy))
        b.Add(c)

def P(x, y): return VECTOR2I(MM(OX + x), MM(OY + y))

# outline = union(rails, boards, tabs)
top_rail = box(x0, y0 - GAP - RAIL, x1, y0 - GAP)
bot_y = y1 + (N - 1) * PITCH_Y
bot_rail = box(x0, bot_y + GAP, x1, bot_y + GAP + RAIL)
shapes = [top_rail, bot_rail]
gaps = []                                   # (y_top_of_gap) for every gap
for k in range(N):
    shapes.append(translate(BRD, 0, k * PITCH_Y))
gaps = [y0 - GAP] + [y1 + k * PITCH_Y for k in range(N)]
for gy in gaps:
    for tx in TABS_X:
        shapes.append(box(tx - TABW / 2, gy - 0.01, tx + TABW / 2, gy + GAP + 0.01))
outline = unary_union(shapes)
assert outline.geom_type == 'Polygon', outline.geom_type
for ring in [outline.exterior] + list(outline.interiors):      # interiors = closed milling slots between tabs
    pts = list(ring.coords)
    for a, c in zip(pts, pts[1:]):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(P(*a)); s.SetEnd(P(*c)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); b.Add(s)
print('outline: 1 exterior, %d milled slots' % len(outline.interiors))

# helper footprint with NPTH holes
def npth_fp(ref, holes, d):
    f = pcbnew.FOOTPRINT(b); f.SetReference(ref); f.SetValue(ref)
    b.Add(f)
    for (hx, hy) in holes:
        pd = pcbnew.PAD(f); pd.SetAttribute(pcbnew.PAD_ATTRIB_NPTH); pd.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pd.SetSize(VECTOR2I(MM(d), MM(d))); pd.SetDrillSize(VECTOR2I(MM(d), MM(d)))
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Mask); ls.AddLayer(pcbnew.B_Mask); pd.SetLayerSet(ls)
        f.Add(pd); pd.SetPos0(P(hx, hy)); pd.SetPosition(P(hx, hy))
    f.Reference().SetVisible(False); f.Value().SetVisible(False)
    f.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_BOARD_ONLY)
    return f

# mouse bites: 0.5 mm holes, 0.8 mm pitch, on both break lines of every tab (centre on the board/rail edge)
mb = []
for gy in gaps:
    for tx in TABS_X:
        for edge in (gy, gy + GAP):
            n = 7
            for i in range(n):
                mb.append((tx - 2.4 + i * 0.8, edge))
npth_fp('MB', mb, 0.5)

# copper keep-out at each tab, both layers, so breaking cannot tear copper
def keepout(xa, ya, xb, yb):
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True)
    z.SetDoNotAllowCopperPour(True); z.SetDoNotAllowTracks(False); z.SetDoNotAllowVias(True)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
    ol = z.Outline(); ol.NewOutline()
    for (x, y) in ((xa, ya), (xb, ya), (xb, yb), (xa, yb)): ol.Append(MM(OX + x), MM(OY + y))
    b.Add(z)
for k in range(N):
    yt, yb_ = y0 + k * PITCH_Y, y1 + k * PITCH_Y
    for tx in TABS_X:
        keepout(tx - TABW / 2 - 0.5, yt, tx + TABW / 2 + 0.5, yt + KEEP_DEPTH)
        keepout(tx - TABW / 2 - 0.5, yb_ - KEEP_DEPTH, tx + TABW / 2 + 0.5, yb_)

# rails: tooling holes 1.152 mm (3 of 4 corners, asymmetric) + 3 fiducials
ty_top, ty_bot = y0 - GAP - RAIL / 2, bot_y + GAP + RAIL / 2
npth_fp('TH', [(x0 + 5, ty_top), (x1 - 5, ty_top), (x0 + 5, ty_bot)], 1.152)
FID = '/usr/share/kicad/footprints/Fiducial.pretty'
for i, (fx, fy) in enumerate([(x0 + 12, ty_top), (x1 - 12, ty_top), (x0 + 12, ty_bot)], 1):
    f = pcbnew.FootprintLoad(FID, 'Fiducial_1mm_Mask2mm')
    f.SetReference('FID%d' % i); b.Add(f); f.SetPosition(P(fx, fy))
    f.Reference().SetVisible(False); f.Value().SetVisible(False)
    f.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)

# rail text
t = pcbnew.PCB_TEXT(b); t.SetText('%s panel %dx  -  break at mouse bites' % (NAME, N))
t.SetPosition(P((x0 + x1) / 2, ty_bot)); t.SetLayer(pcbnew.F_SilkS)
t.SetTextSize(VECTOR2I(MM(1.2), MM(1.2))); t.SetTextThickness(MM(0.18)); b.Add(t)

# check: nothing but pours may sit where the tabs break off
bad = 0
for k in range(N):
    yt, yb_ = y0 + k * PITCH_Y, y1 + k * PITCH_Y
    for tx in TABS_X:
        for (ya, yb2) in ((yt, yt + KEEP_DEPTH), (yb_ - KEEP_DEPTH, yb_)):
            r = box(tx - TABW / 2 - 0.5, ya, tx + TABW / 2 + 0.5, yb2)
            for t in b.GetTracks():
                if t.GetClass() == 'PCB_TRACK':
                    from shapely.geometry import LineString
                    ls_ = LineString([(ToMM(t.GetStart().x) - OX, ToMM(t.GetStart().y) - OY), (ToMM(t.GetEnd().x) - OX, ToMM(t.GetEnd().y) - OY)]).buffer(ToMM(t.GetWidth()) / 2)
                else:
                    ls_ = box(ToMM(t.GetPosition().x) - OX - 0.5, ToMM(t.GetPosition().y) - OY - 0.5, ToMM(t.GetPosition().x) - OX + 0.5, ToMM(t.GetPosition().y) - OY + 0.5)
                if ls_.intersects(r):
                    bad += 1; print('COPPER AT TAB x=%.1f board %d: %s %s' % (tx, k + 1, t.GetClass(), t.GetNetname()))
            for f in b.GetFootprints():
                for pd in f.Pads():
                    if pd.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH: continue
                    bbp = pd.GetBoundingBox()
                    pb = box(ToMM(bbp.GetX()) - OX, ToMM(bbp.GetY()) - OY, ToMM(bbp.GetRight()) - OX, ToMM(bbp.GetBottom()) - OY)
                    if pb.intersects(r):
                        bad += 1; print('PAD AT TAB x=%.1f board %d: %s' % (tx, k + 1, f.GetReference()))
print('tab check:', 'OK' if bad == 0 else '%d problems' % bad)
ds = b.GetDesignSettings()
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out_file)
print('panel %.2f x %.2f mm, %d boards' % (w, bot_y + GAP + RAIL - (y0 - GAP - RAIL), N))
