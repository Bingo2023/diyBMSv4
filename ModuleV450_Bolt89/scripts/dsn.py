#!/usr/bin/env python3
"""Minimal Specctra DSN exporter / SES importer for KiCad 7 boards (headless).
usage: dsn.py export board.kicad_pcb out.dsn
       dsn.py import board.kicad_pcb in.ses out.kicad_pcb
"""
import sys, re
import pcbnew
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union

U = lambda v: pcbnew.ToMM(v) * 1000.0     # internal -> um
def XY(v): return (U(v.x), -U(v.y))

LAYERS = {pcbnew.F_Cu: 'F.Cu', pcbnew.B_Cu: 'B.Cu'}
VIA_SIG = ('Via[0-1]_700:350_um', 700, 350)
VIA_PWR = ('Via[0-1]_1000:500_um', 1000, 500)
POWER_W = 1500

def q(s):
    return '"%s"' % s

def outline_polygon(b):
    sps = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(sps)
    o = sps.Outline(0)
    pts = [XY(o.CPoint(i)) for i in range(o.PointCount())]
    return Polygon(pts)

def pad_shape(pad, layer):
    sz = pad.GetSize(); w, h = U(sz.x), U(sz.y)
    ang = round(pad.GetOrientation().AsDegrees()) % 180
    if ang == 90: w, h = h, w
    sh = pad.GetShape()
    if sh == pcbnew.PAD_SHAPE_CIRCLE:
        return '(circle %s %.1f)' % (layer, w)
    if sh == pcbnew.PAD_SHAPE_OVAL and abs(w - h) > 1:
        r = min(w, h)
        if w > h: return '(path %s %.1f %.1f 0 %.1f 0)' % (layer, r, -(w - h) / 2, (w - h) / 2)
        return '(path %s %.1f 0 %.1f 0 %.1f)' % (layer, r, -(h - w) / 2, (h - w) / 2)
    return '(rect %s %.1f %.1f %.1f %.1f)' % (layer, -w / 2, -h / 2, w / 2, h / 2)

def export(b, out):
    lines = []
    A = lines.append
    A('(pcb board\n  (parser (string_quote ") (space_in_quoted_tokens on) (host_cad "KiCad") (host_version "7"))')
    A('  (resolution um 10)\n  (unit um)\n  (structure')
    A('    (layer F.Cu (type signal) (property (index 0)))')
    A('    (layer B.Cu (type signal) (property (index 1)))')
    poly = outline_polygon(b).buffer(-300, join_style=2)   # keep 0.3 mm from edge
    pts = ' '.join('%.1f %.1f' % p for p in list(poly.exterior.coords))
    A('    (boundary (path pcb 0 %s))' % pts)
    # planes from zones that are marked as router planes (priority>=1 & big)
    for z in b.Zones():
        if z.GetNetname() and z.GetZoneName().startswith('PLANE'):
            o = z.Outline().Outline(0)
            zp = Polygon([XY(o.CPoint(i)) for i in range(o.PointCount())]).intersection(outline_polygon(b))
            if zp.geom_type != 'Polygon': zp = max(zp.geoms, key=lambda g: g.area)
            A('    (plane %s (polygon %s 0 %s))' % (q(z.GetNetname()), LAYERS[z.GetLayer()],
              ' '.join('%.1f %.1f' % p for p in list(zp.exterior.coords))))
    # board cut-outs (milled bolt holes) -> keepouts
    sps = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(sps)
    for hi in range(sps.HoleCount(0)):
        h = sps.CHole(0, hi)
        hp = Polygon([XY(h.CPoint(i)) for i in range(h.PointCount())]).buffer(300)
        A('    (keepout "" (polygon signal 0 %s))' % ' '.join('%.1f %.1f' % p for p in list(hp.exterior.coords)))
    # NPTH holes -> keepouts
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                x, y = XY(p.GetPosition())
                A('    (keepout "" (circle signal %.1f %.1f %.1f))' % (U(p.GetDrillSize().x) + 400, x, y))
    A('    (via %s %s)' % (q(VIA_SIG[0]), q(VIA_PWR[0])))
    A('    (rule (width 300) (clearance 200) (clearance 200 (type default_smd)) (clearance 50 (type smd_smd)))')
    A('  )')
    # placement: every footprint gets its own image with pre-rotated pins, placed at 0 rotation
    padstacks = {}
    images = []
    A('  (placement')
    netpins = {}
    for i, f in enumerate(b.GetFootprints()):
        cu = [p for p in f.Pads() if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]
        if not cu: continue
        ref = f.GetReference()
        img = 'IMG_%d_%s' % (i, re.sub(r'[^A-Za-z0-9_]', '_', ref))
        fx, fy = XY(f.GetPosition())
        A('    (component %s (place %s %.1f %.1f front 0))' % (q(img), q(ref), fx, fy))
        pins = []
        seen = {}
        for p in cu:
            layers = []
            if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH,):
                layers = ['F.Cu', 'B.Cu']
            else:
                layers = ['F.Cu'] if p.IsOnLayer(pcbnew.F_Cu) else ['B.Cu']
            shapes = ' '.join(pad_shape(p, L) for L in layers)
            key = shapes
            if key not in padstacks:
                padstacks[key] = 'PS%d' % len(padstacks)
            num = p.GetNumber() or 'x'
            seen[num] = seen.get(num, 0) + 1
            pname = num if seen[num] == 1 else '%s@%d' % (num, seen[num] - 1)
            px, py = XY(p.GetPosition())
            pins.append('      (pin %s %s %.1f %.1f)' % (padstacks[key], q(pname), px - fx, py - fy))
            if p.GetNetname():
                netpins.setdefault(p.GetNetname(), []).append('%s-%s' % (q(ref), q(pname)))
        images.append('    (image %s\n%s\n    )' % (q(img), '\n'.join(pins)))
    A('  )')
    A('  (library')
    lines.extend(images)
    for key, name in padstacks.items():
        A('    (padstack %s (shape %s) (attach off))' % (q(name), ') (shape '.join(re.findall(r'\((?:circle|rect|path)[^()]*\)', key))))
    for vn, d, dr in (VIA_SIG, VIA_PWR):
        A('    (padstack %s (shape (circle F.Cu %d)) (shape (circle B.Cu %d)) (attach off))' % (q(vn), d, d))
    A('  )')
    A('  (network')
    for n, pins in netpins.items():
        A('    (net %s (pins %s))' % (q(n), ' '.join(pins)))
    pwr = [n for n in netpins if re.match(r'^(BAT\+|DRAIN|S\d_\d)$', n)]
    sup = [n for n in netpins if n in ('VCC', 'GND')]
    sig = [n for n in netpins if n not in pwr and n not in sup]
    A('    (class kicad_default %s (circuit (use_via %s)) (rule (width 300) (clearance 200)))' % (' '.join(map(q, sig)), q(VIA_SIG[0])))
    A('    (class Supply %s (circuit (use_via %s)) (rule (width 500) (clearance 200)))' % (' '.join(map(q, sup)), q(VIA_SIG[0])))
    A('    (class Power %s (circuit (use_via %s)) (rule (width %d) (clearance 300)))' % (' '.join(map(q, pwr)), q(VIA_PWR[0]), POWER_W))
    A('  )')
    A('  (wiring')
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_TRACK' and t.IsLocked():
            (x1, y1), (x2, y2) = XY(t.GetStart()), XY(t.GetEnd())
            A('    (wire (path %s %.1f %.1f %.1f %.1f %.1f) (net %s) (type protect))' % (LAYERS[t.GetLayer()], U(t.GetWidth()), x1, y1, x2, y2, q(t.GetNetname())))
    A('  )\n)')
    open(out, 'w').write('\n'.join(lines) + '\n')

# ------------------------------------------------------------- SES import
def sexp(s):
    toks = re.findall(r'\(|\)|"[^"]*"|[^\s()]+', s)
    st = [[]]
    for t in toks:
        if t == '(':
            st.append([])
        elif t == ')':
            x = st.pop(); st[-1].append(x)
        else:
            st[-1].append(t.strip('"'))
    return st[0][0]

def find(node, name):
    for c in node:
        if isinstance(c, list) and c and c[0] == name:
            yield c

def do_import(b, ses):
    t = sexp(open(ses).read())
    routes = next(find(t, 'routes'))
    res = next(find(routes, 'resolution'))
    scale = float(res[2])                 # units per um
    k = lambda v: pcbnew.FromMM(float(v) / scale / 1000.0)
    netout = next(find(routes, 'network_out'))
    nw = nv = 0
    for n in find(netout, 'net'):
        net = b.FindNet(n[1])
        for w in find(n, 'wire'):
            if any(isinstance(c, list) and c[:2] == ['type', 'protect'] for c in w):
                continue
            path = next(find(w, 'path'))
            layer = pcbnew.F_Cu if path[1] == 'F.Cu' else pcbnew.B_Cu
            width = k(path[2]); c = path[3:]
            pts = [(k(c[i]), -k(c[i + 1])) for i in range(0, len(c) - 1, 2)]
            for a, bb in zip(pts, pts[1:]):
                tr = pcbnew.PCB_TRACK(b)
                tr.SetStart(pcbnew.VECTOR2I(*a)); tr.SetEnd(pcbnew.VECTOR2I(*bb))
                tr.SetWidth(width); tr.SetLayer(layer); tr.SetNet(net); b.Add(tr); nw += 1
        for v in find(n, 'via'):
            name = v[1]
            d, dr = (1000, 500) if '1000' in name else (700, 350)
            via = pcbnew.PCB_VIA(b)
            via.SetPosition(pcbnew.VECTOR2I(k(v[2]), -k(v[3])))
            via.SetWidth(pcbnew.FromMM(d / 1000)); via.SetDrill(pcbnew.FromMM(dr / 1000))
            via.SetNet(net); b.Add(via); nv += 1
    print('imported', nw, 'segments', nv, 'vias')

if __name__ == '__main__':
    b = pcbnew.LoadBoard(sys.argv[2])
    if sys.argv[1] == 'export':
        export(b, sys.argv[3])
    else:
        locked = [((t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)) for t in b.GetTracks() if t.IsLocked()]
        for tr in list(b.GetTracks()):
            if not tr.IsLocked(): b.Remove(tr)
        do_import(b, sys.argv[3])
        filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
        b.Save(sys.argv[4])
