#!/usr/bin/env python3
"""ModuleV450_Bolt89: bolt-on cell module, 89 mm bolt spacing, rectangular outline (derived from Bolt123_V1).
- Load block (16x 2512 3R, 4S4P) + MOSFET concentrated at the Minus side (x 50..100)
- MCU / reference / opto / sensors in a quiet zone at the Plus side (x 12..48)
- Power paths are solid copper zones (VCC feed strip, VCC bus, series nodes, DRAIN bus, source tongue)
- Load return: Q1 source -> top GND tongue -> Minus bolt (not through the MCU ground plane)
- MCU supply: separate branch from fuse via TVS (star point at F1)
- Bottom: GND plane, connected to the Minus bolt (star)
Bolt spacing 89 mm, holes 6.3 mm plated, outline 120.5 x 31.5 mm rectangle.
Rev 2: rounded ends (like Bolt123), compact MCU zone, load block moved left, Q1 between load and Minus bolt
(>= 5 mm from the bolt ring), load columns 8.2 mm pitch.
"""
import math, sys, json
import pcbnew
from pcbnew import VECTOR2I, FromMM as MM

LIB = '/usr/share/kicad/footprints/'
OX, OY = 60.0, 100.0
PITCH = 89.0
HOLE = 6.3
RING = 15.0
HALF = 15.75
TAB_X0, TAB_X1, TAB_Y1 = 11.0, 18.0, 28.5

def P(x, y):
    return VECTOR2I(MM(OX + x), MM(OY + y))

board = pcbnew.BOARD()
board.SetCopperLayerCount(2)
ds = board.GetDesignSettings()

nets = {}
def net(name):
    if name not in nets:
        n = pcbnew.NETINFO_ITEM(board, name)
        board.Add(n)
        nets[name] = n
    return nets[name]

BOM = {}
def place(lib, fpname, ref, value, x, y, rot, pads, lcsc='', populate=True, libpath=None):
    f = pcbnew.FootprintLoad(libpath or (LIB + lib + '.pretty'), fpname)
    if f is None:
        sys.exit('footprint missing %s:%s' % (lib, fpname))
    f.SetReference(ref); f.SetValue(value)
    board.Add(f)
    f.SetPosition(P(x, y)); f.SetOrientationDegrees(rot)
    for p in f.Pads():
        n = pads.get(p.GetNumber())
        if n:
            p.SetNet(net(n))
    if not populate:
        f.SetAttributes(f.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM)
    BOM[ref] = (value, lcsc, populate, fpname)
    return f

def bolt(ref, x, y, netname):
    """6.5 mm bolt hole as milled cut-out (JLC max. drill is 6.3 mm), exposed copper ring
    (15 mm, from the zones, both sides, mask-opened) and 16 plated stitching holes."""
    f = pcbnew.FOOTPRINT(board)
    f.SetReference(ref); f.SetValue('M6 bolt %.1fmm' % HOLE)
    board.Add(f)
    def pad(px, py, size, drill, layers, attr):
        pd = pcbnew.PAD(f)
        pd.SetNumber('1'); pd.SetShape(pcbnew.PAD_SHAPE_CIRCLE); pd.SetAttribute(attr)
        pd.SetSize(VECTOR2I(MM(size), MM(size)))
        if drill: pd.SetDrillSize(VECTOR2I(MM(drill), MM(drill)))
        ls = pcbnew.LSET(); [ls.AddLayer(l) for l in layers]
        pd.SetLayerSet(ls); pd.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        f.Add(pd)
        pd.SetPos0(VECTOR2I(MM(px), MM(py))); pd.SetPosition(VECTOR2I(MM(px), MM(py)))
        if drill: pd.SetNet(net(netname))
        return pd
    # plated 6.3 mm hole with 15 mm contact ring on both sides
    pad(0, 0, RING, HOLE, (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.F_Mask, pcbnew.B_Mask), pcbnew.PAD_ATTRIB_PTH)
    for i in range(16):
        a = 2 * math.pi * i / 16
        pad(5.6 * math.cos(a), 5.6 * math.sin(a), 1.0, 0.6,
            (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.F_Mask, pcbnew.B_Mask), pcbnew.PAD_ATTRIB_PTH)
    f.SetPosition(P(x, y))
    f.Reference().SetVisible(False); f.Value().SetVisible(False)
    f.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES)

bolt('BAT+', 0, 0, 'BAT+')
bolt('BAT-', PITCH, 0, 'GND')

# ------------------------------------------------------------ load block (Minus side)
R3 = 'C46193'                       # 1R2 1% 1W 2512 UniOhm 25121WF120KT4E (as BMS_alt)
ROWS = [-11.5, -3.9, 3.9, 11.5]
COLS = [39.6, 47.8, 56.0, 64.2]
BUS_L, BUS_R = 34.3, 37.6           # VCC bus
DR_L, DR_R = 66.2, 69.5             # DRAIN bus
ref = 6
for si, y in enumerate(ROWS, 1):
    chain = ['VCC'] + ['S%d_%d' % (si, k) for k in (1, 2, 3)] + ['DRAIN']
    for k, x in enumerate(COLS):
        place('Resistor_SMD', 'R_2512_6332Metric', 'R%d' % ref, '1R2', x, y, 0,
              {'1': chain[k], '2': chain[k + 1]}, R3)
        ref += 1
# Q1: AO4402 SO-8 between DRAIN bus and Minus bolt, drain pins (5-8) left, source (1-3) right, gate pin 4 top right
place('Package_SO', 'SOIC-8_3.9x4.9mm_P1.27mm', 'Q1', 'AO4402', 73.0, 0.0, 180,
      {'1': 'GND', '2': 'GND', '3': 'GND', '4': 'GATE', '5': 'DRAIN', '6': 'DRAIN', '7': 'DRAIN', '8': 'DRAIN'}, 'C115828')
place('Resistor_SMD', 'R_0805_2012Metric', 'R36', '10K', 76.5, -4.5, 180, {'1': 'GND', '2': 'GATE'}, 'C17414')
place('Resistor_SMD', 'R_0805_2012Metric', 'R35', '510R', 76.5, -7.0, 180, {'1': 'DUMP', '2': 'GATE'}, 'C17734')

# ------------------------------------------------------------ input (Plus side)
place('Fuse', 'Fuse_2920_7451Metric', 'F1', '2920L500/30GR 5A', 13.5, -12.3, 0, {'1': 'BAT+', '2': 'VCC'}, 'C19078763')
place('Diode_SMD', 'D_SMB', 'D2', 'SMBJ5.0A', 16.0, -6.6, 0, {'1': 'VCC', '2': 'GND'}, 'C440263')

# ------------------------------------------------------------ quiet zone (compact): MCU & analog, x 9.5 .. 34
UX = 21.0
place('Package_SO', 'SOIC-14_3.9x8.7mm_P1.27mm', 'U2', 'ATTINY1624-SSU', UX, 3.0, 90,
      {'1': 'VCC', '3': 'VREF', '4': 'PA6', '5': 'PA7', '6': 'RXD0', '7': 'TXD0',
       '8': 'DUMP', '9': 'ENABLE', '10': 'RESET', '11': 'REF_EN', '13': 'PA3', '14': 'GND'}, 'C5160891')
place('Capacitor_SMD', 'C_0805_2012Metric', 'C1', '100nF', UX - 6.0, 3.0, 90, {'1': 'VCC', '2': 'GND'}, 'C49678')
place('Capacitor_SMD', 'C_0805_2012Metric', 'C2', '10uF', UX - 8.4, 3.0, 90, {'1': 'VCC', '2': 'GND'}, 'C15850')
place('Connector_PinSocket_2.54mm', 'PinSocket_1x03_P2.54mm_Vertical', 'UPDI1', 'UPDI', 20.0, -2.55, 90,
      {'1': 'VCC', '2': 'RESET', '3': 'GND'}, '', populate=False)
place('Package_TO_SOT_SMD', 'SOT-23', 'D1', 'TLV431BQDBZR', 28.8, -7.0, 0, {'1': 'VREF', '2': 'VREF', '3': 'GND'}, 'C398374')
place('Resistor_SMD', 'R_0805_2012Metric', 'R2', '1K', 28.6, -2.6, 0, {'1': 'REF_EN', '2': 'VREF'}, 'C17513')
place('LED_SMD', 'LED_0805_2012Metric', 'D4', 'Yellow', 21.6, -7.0, 180, {'1': 'LED_B', '2': 'PA6'}, 'C2296')
place('Resistor_SMD', 'R_0805_2012Metric', 'R34', '2K2', 25.1, -7.0, 180, {'1': 'GND', '2': 'LED_B'}, 'C17520')
place('Resistor_SMD', 'R_0805_2012Metric', 'R5', '200R', 28.0, 0.5, 0, {'1': 'OPTO_A', '2': 'TXD0'}, 'C17540')
place('Resistor_SMD', 'R_0805_2012Metric', 'R1', '100K', 28.0, 3.0, 180, {'1': 'VCC', '2': 'RESET'}, 'C149504')
place('Resistor_SMD', 'R_0805_2012Metric', 'R30', '2K2', 28.0, 5.5, 0, {'1': 'GND', '2': 'RXD0'}, 'C17520')
place('Resistor_SMD', 'R_0805_2012Metric', 'R31', '10K', 31.0, 1.5, 90, {'1': 'PA3', '2': 'GND'}, 'C17414')
# board/load temperature sensor at the edge of the quiet zone, right next to the VCC bus / load block
place('Resistor_SMD', 'R_0805_2012Metric', 'R32', 'NTC 10K B3950', 33.2, -2.6, 90, {'1': 'ENABLE', '2': 'PA7'}, 'C51597')
place('Resistor_SMD', 'R_0805_2012Metric', 'R33', '10K', 33.2, 1.5, 90, {'1': 'PA7', '2': 'GND'}, 'C17414')
# opto standing upright between TX1 and RX1 (pin 1/2 up towards the MCU, pins 3/4 down towards TX1)
place('Package_SO', 'SOP-4_4.4x2.6mm_P1.27mm', 'U1', 'LTV-217-B-G', 22.15, 11.2, 270,
      {'1': 'OPTO_A', '2': 'GND', '3': 'TXOUT1', '4': 'TXOUT2'}, 'C115450')
PB = 'Molex_PicoBlade_53261-0271_1x02-1MP_P1.25mm_Horizontal'
place('Connector_Molex', PB, 'TX1', 'PicoBlade 2P', 15.8, 12.4, 0, {'1': 'TXOUT1', '2': 'TXOUT2'}, 'C177225')
place('Connector_Molex', PB, 'RX1', 'PicoBlade 2P', 28.5, 12.4, 0, {'1': 'RXD0', '2': 'VCC'}, 'C177225')
place('LED_SMD', 'LED_0805_2012Metric', 'D3', 'Red', 32.3, 7.6, 0, {'1': 'LED_R', '2': 'VCC'}, 'C84256')
place('Resistor_SMD', 'R_0805_2012Metric', 'R37', '2K2', 71.0, 12.5, 90, {'1': 'LED_R', '2': 'DRAIN'}, 'C17520')
# cell temperature NTC next to the Plus bolt (thermal copper below on B.Cu)
place('Resistor_SMD', 'R_0805_2012Metric', 'R23', 'NTC 10K B3950', 10.0, 12.6, 90, {'1': 'ENABLE', '2': 'PA3'}, 'C51597')
place('Resistor_SMD', 'R_0805_2012Metric', 'R23B', 'NTC 10K B3950 DNP', 33.2, -7.0, 90, {'1': 'ENABLE', '2': 'PA3'}, 'C51597', populate=False)

place('', 'diybms_logo_24x10mm', 'G1', 'LOGO', 21.0, -3.0, 0, {}, '', populate=False,
      libpath='/home/claude/repo/ModuleV450/ModuleV450.pretty')
logo = [f for f in board.GetFootprints() if f.GetReference() == 'G1'][0]
logo.Flip(logo.GetPosition(), False)
logo.Reference().SetVisible(False); logo.Value().SetVisible(False)
logo.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_BOARD_ONLY)

for _f in board.GetFootprints():
    if _f.GetReference() == 'UPDI1':
        for _p in _f.Pads():
            if _p.GetNumber() == '3': _p.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
def pp(ref, num):
    f = [f for f in board.GetFootprints() if f.GetReference() == ref][0]
    p = [p for p in f.Pads() if p.GetNumber() == num][0].GetPosition()
    return (round(pcbnew.ToMM(p.x) - OX, 4), round(pcbnew.ToMM(p.y) - OY, 4))

# ------------------------------------------------------------ outline: rounded ends (like Bolt123)
def seg(a, b):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(P(*a)); s.SetEnd(P(*b)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); board.Add(s)
def arc(c, start):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetCenter(P(*c)); s.SetStart(P(*start)); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(180, pcbnew.DEGREES_T), True)
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); board.Add(s)
seg((0, -HALF), (PITCH, -HALF))
arc((PITCH, 0), (PITCH, -HALF))
seg((PITCH, HALF), (0, HALF))
arc((0, 0), (0, HALF))

# ------------------------------------------------------------ copper zones
def zone(netname, layer, pts, prio, clearance=0.3, plane=True, solid=True):
    z = pcbnew.ZONE(board)
    z.SetZoneName(('PLANE_' if plane else 'FILL_') + netname)
    z.SetLayer(layer); z.SetNet(net(netname)); z.SetAssignedPriority(prio)
    ol = z.Outline(); ol.NewOutline()
    for (x, y) in pts: ol.Append(MM(OX + x), MM(OY + y))
    z.SetLocalClearance(MM(clearance)); z.SetMinThickness(MM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if solid else pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.4)); z.SetThermalReliefSpokeWidth(MM(0.8))
    board.Add(z)
BIG = 20
F, B = pcbnew.F_Cu, pcbnew.B_Cu
for L in (F, B):
    zone('BAT+', L, [(-BIG, -BIG), (9.0, -BIG), (9.0, BIG), (-BIG, BIG)], 3)
# bottom side: Plus-pole copper under R23 = thermal path from the cell terminal to the NTC
zone('BAT+', B, [(7.5, 10.4), (12.0, 10.4), (12.0, BIG), (7.5, BIG)], 3)
# Minus bolt area (top) + source tongue from Q1 pins 1-3
zone('GND', F, [(78.5, -BIG), (PITCH + BIG, -BIG), (PITCH + BIG, BIG), (78.5, BIG)], 3)
zone('GND', F, [(74.2, -1.25), (79.0, -1.25), (79.0, 10.0), (74.2, 10.0)], 2)
# VCC: feed strip along the top edge + vertical bus left of the load block
zone('VCC', F, [(15.6, -15.4), (BUS_R, -15.4), (BUS_R, 13.8), (BUS_L, 13.8), (BUS_L, -9.4), (15.6, -9.4)], 2)
# F1 moved off the bolt area (as Bolt123): BAT+ tongue from the bolt ring to F1 pad 1
zone('BAT+', F, [(8.0, -15.4), (11.1, -15.4), (11.1, -9.6), (8.0, -9.6)], 3)
for si, y in enumerate(ROWS, 1):
    for k in range(3):
        x0, x1 = COLS[k] + 2.0, COLS[k + 1] - 2.0
        zone('S%d_%d' % (si, k + 1), F, [(x0, y - 2.1), (x1, y - 2.1), (x1, y + 2.1), (x0, y + 2.1)], 2)
# DRAIN bus right of the load block + tongue to the Q1 drain pins
zone('DRAIN', F, [(DR_L, -13.8), (DR_R, -13.8), (DR_R, -2.6), (71.7, -2.6), (71.7, 2.6), (DR_R, 2.6), (DR_R, 13.8), (DR_L, 13.8)], 2)
# bottom: GND plane (signal reference), star-connected at the Minus bolt
zone('GND', B, [(9.6, -BIG), (PITCH + BIG, -BIG), (PITCH + BIG, BIG), (9.6, BIG)], 1, solid=False)

# ------------------------------------------------------------ pre-routed tracks
def track(netname, pts, w, layer=F):
    for a, b in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board); t.SetStart(P(*a)); t.SetEnd(P(*b))
        t.SetWidth(MM(w)); t.SetLayer(layer); t.SetNet(net(netname)); t.SetLocked(True); board.Add(t)
f2, d2a = pp('F1', '2'), pp('D2', '1')
track('VCC', [(f2[0], f2[1]), (f2[0], -9.0), (d2a[0], -9.0), d2a], 1.2)
# star branch: TVS -> C2 (10u) -> C1 (100n) -> U2 pin 1 (trunk runs left of C2)
c2v, c1v, u1v = pp('C2', '1'), pp('C1', '1'), pp('U2', '1')
c2g, c1g, u14 = pp('C2', '2'), pp('C1', '2'), pp('U2', '14')
TX = c2v[0] - 2.1
track('VCC', [d2a, (d2a[0], -3.0), (TX, -3.0), (TX, c2v[1]), c2v], 0.8)
track('VCC', [c2v, c1v], 0.8)
track('VCC', [c1v, (c1v[0] + 0.9, c1v[1] + 0.9), (c1v[0] + 1.6, u1v[1]), u1v], 0.5)
track('GND', [c2g, c1g], 0.8)
track('GND', [c1g, (c1g[0], c1g[1] - 0.85), (c1g[0] + 0.68, u14[1]), u14], 0.5)
# small fixed stubs
r37d = pp('R37', '2'); track('DRAIN', [r37d, (DR_R - 0.5, r37d[1])], 0.6)
d3v = pp('D3', '2'); track('VCC', [d3v, (BUS_L + 0.5, d3v[1])], 0.5)
qg, r36g, r35g, r36gnd = pp('Q1', '4'), pp('R36', '2'), pp('R35', '2'), pp('R36', '1')
track('GATE', [qg, (r36g[0], qg[1] - 0.6), r36g, r35g], 0.4)
track('GND', [r36gnd, (79.0, r36gnd[1])], 0.5)
for r in ('Q1', 'R36', 'R35', 'C1', 'C2', 'D2', 'R37', 'D3', 'U1'):
    print(r, [(p.GetNumber(), pp(r, p.GetNumber())) for p in [f for f in board.GetFootprints() if f.GetReference() == r][0].Pads()])
# ------------------------------------------------------------ rules / net classes
ds.m_MinClearance = MM(0.2); ds.m_TrackMinWidth = MM(0.2)
ds.m_ViasMinSize = MM(0.6); ds.m_MinThroughDrill = MM(0.3); ds.m_CopperEdgeClearance = MM(0.3)
nc = ds.m_NetSettings
d = nc.m_DefaultNetClass
d.SetClearance(MM(0.2)); d.SetTrackWidth(MM(0.3)); d.SetViaDiameter(MM(0.7)); d.SetViaDrill(MM(0.35))
pwr = pcbnew.NETCLASS('Power')
pwr.SetClearance(MM(0.3)); pwr.SetTrackWidth(MM(1.5)); pwr.SetViaDiameter(MM(1.0)); pwr.SetViaDrill(MM(0.5))
nc.m_NetClasses['Power'] = pwr
for n in ['VCC', 'BAT+', 'GND', 'DRAIN'] + ['S%d_%d' % (s, k) for s in range(1, 5) for k in (1, 2, 3)]:
    nets[n].SetNetClass(pwr)

# ------------------------------------------------------------ silkscreen
def text(s, x, y, layer, size=1.2, mirror=False, thick=0.18):
    t = pcbnew.PCB_TEXT(board); t.SetText(s); t.SetPosition(P(x, y)); t.SetLayer(layer)
    t.SetTextSize(VECTOR2I(MM(size), MM(size))); t.SetTextThickness(MM(thick)); t.SetMirrored(mirror); board.Add(t)
FS, BS = pcbnew.F_SilkS, pcbnew.B_SilkS
text('+', -11.5, 0.0, FS, 3.0, thick=0.4); text('-', 100.5, 0.0, FS, 3.0, thick=0.4)
text('+', -11.5, 0.0, BS, 3.0, True, 0.4); text('-', 100.5, 0.0, BS, 3.0, True, 0.4)
text('HOT!', 51.9, 0.0, FS, 1.2)
text('ModuleV450_Bolt89', 52.0, -6.0, BS, 1.5, True, 0.25)
text('DIYBMS v4.5 cell module, 89mm bolt spacing', 52.0, -3.0, BS, 1.0, True)
text('after BMS_alt v1.7 (Jau/Vas)', 52.0, -0.5, BS, 1.0, True)
text('load 4S4P 16x 1R2 = 1R2 (~3A)', 52.0, 2.0, BS, 1.0, True)
text('JLCJLCJLCJLC', 52.0, 5.0, BS, 1.0, True, 0.15)

out = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/work/b89b/ModuleV450_Bolt89.kicad_pcb'
board.Save(out)
json.dump(BOM, open(out.replace('.kicad_pcb', '_bommap.json'), 'w'), indent=1)
print('saved', out, len(board.GetFootprints()), 'footprints', len(nets), 'nets')
