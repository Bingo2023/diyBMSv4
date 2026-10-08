#!/usr/bin/env python3
"""Post-route fix: every SMD GND pad listed as unconnected in the DRC report gets a short
stub + via to the bottom GND plane, placed in the first free direction."""
import sys, re, math
import pcbnew
from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union

brd, drc, out = sys.argv[1:4]
b = pcbnew.LoadBoard(brd)
MM, TM = pcbnew.FromMM, pcbnew.ToMM
txt = open(drc).read()
want = set(re.findall(r'Pad (\S+) \[GND\] of (\S+) on F\.Cu', txt))
gnd = b.FindNet('GND')

def obstacles(layer, exclude_net):
    geo = []
    for f in b.GetFootprints():
        for p in f.Pads():
            if not p.IsOnLayer(layer) or p.GetNetCode() == exclude_net:
                continue
            bb = p.GetBoundingBox()
            geo.append(box(TM(bb.GetLeft()), TM(bb.GetTop()), TM(bb.GetRight()), TM(bb.GetBottom())))
    for t in b.GetTracks():
        if t.GetNetCode() == exclude_net:
            continue
        if t.GetClass() == 'PCB_VIA':
            geo.append(Point(TM(t.GetPosition().x), TM(t.GetPosition().y)).buffer(TM(t.GetWidth()) / 2))
        elif t.GetLayer() == layer:
            geo.append(LineString([(TM(t.GetStart().x), TM(t.GetStart().y)), (TM(t.GetEnd().x), TM(t.GetEnd().y))]).buffer(TM(t.GetWidth()) / 2))
    for z in b.Zones():
        if z.GetNetCode() != exclude_net and z.IsOnLayer(layer):
            fp = z.GetFilledPolysList(layer)
            for i in range(fp.OutlineCount()):
                o = fp.Outline(i)
                from shapely.geometry import Polygon
                pts = [(TM(o.CPoint(k).x), TM(o.CPoint(k).y)) for k in range(o.PointCount())]
                if len(pts) > 2:
                    geo.append(Polygon(pts).buffer(0))
    return unary_union(geo)

# board edge keep-in
sps = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(sps)
from shapely.geometry import Polygon
o = sps.Outline(0)
inside = Polygon([(TM(o.CPoint(k).x), TM(o.CPoint(k).y)) for k in range(o.PointCount())]).buffer(-0.8)
obsF = obstacles(pcbnew.F_Cu, gnd.GetNetCode())
obsB = obstacles(pcbnew.B_Cu, gnd.GetNetCode())
added = 0
for num, ref in want:
    fp = [f for f in b.GetFootprints() if f.GetReference() == ref][0]
    pad = [p for p in fp.Pads() if p.GetNumber() == num][0]
    px, py = TM(pad.GetPosition().x), TM(pad.GetPosition().y)
    done = False
    for dist in (1.3, 1.6, 2.0, 2.5):
        for k in range(16):
            a = 2 * math.pi * k / 16
            vx, vy = px + dist * math.cos(a), py + dist * math.sin(a)
            via_g = Point(vx, vy).buffer(0.35 + 0.2)
            stub = LineString([(px, py), (vx, vy)]).buffer(0.2 + 0.2)
            if not inside.contains(Point(vx, vy)):
                continue
            if via_g.intersects(obsF) or via_g.intersects(obsB):
                continue
            # stub may touch its own pad only
            own = box(TM(pad.GetBoundingBox().GetLeft()), TM(pad.GetBoundingBox().GetTop()),
                      TM(pad.GetBoundingBox().GetRight()), TM(pad.GetBoundingBox().GetBottom()))
            if stub.difference(own.buffer(0.05)).intersects(obsF):
                continue
            t = pcbnew.PCB_TRACK(b); t.SetStart(pad.GetPosition())
            t.SetEnd(pcbnew.VECTOR2I(MM(vx), MM(vy))); t.SetWidth(MM(0.4)); t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd); b.Add(t)
            v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(MM(vx), MM(vy)))
            v.SetWidth(MM(0.7)); v.SetDrill(MM(0.35)); v.SetNet(gnd); b.Add(v)
            print('GND via for %s.%s at %.2f %.2f' % (ref, num, vx - 60, vy - 100)); added += 1
            done = True
            break
        if done:
            break
    if not done:
        print('no room for', ref, num)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
pcbnew.WriteDRCReport(b, out.replace('.kicad_pcb', '_drc.txt'), pcbnew.EDA_UNITS_MILLIMETRES, True)
print('added', added)
