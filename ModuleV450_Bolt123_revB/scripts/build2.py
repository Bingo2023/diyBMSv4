#!/usr/bin/env python3
"""ModuleV450 bolt-on, rev B: EMC-oriented layout.
- Load block (16x 2512 3R, 4S4P) + MOSFET concentrated at the Minus side (x 50..100)
- MCU / reference / opto / sensors in a quiet zone at the Plus side (x 12..48)
- Power paths are solid copper zones (VCC feed strip, VCC bus, series nodes, DRAIN bus, source tongue)
- Load return: Q1 source -> top GND tongue -> Minus bolt (not through the MCU ground plane)
- MCU supply: separate branch from fuse via TVS (star point at F1)
- Bottom: GND plane, connected to the Minus bolt (star)
Bolt spacing 123 mm, holes 6.5 mm.
"""
import math, sys, json
import pcbnew
from pcbnew import VECTOR2I, FromMM as MM

LIB = '/usr/share/kicad/footprints/'
OX, OY = 60.0, 100.0
PITCH = 123.0
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
COLS = [58.0, 68.0, 78.0, 88.0]
ref = 6
for si, y in enumerate(ROWS, 1):
    chain = ['VCC'] + ['S%d_%d' % (si, k) for k in (1, 2, 3)] + ['DRAIN']
    for k, x in enumerate(COLS):
        place('Resistor_SMD', 'R_2512_6332Metric', 'R%d' % ref, '1R2', x, y, 0,
              {'1': chain[k], '2': chain[k + 1]}, R3)
        ref += 1
# Q1: AO4402 SO-8, 20V 20A, 7mOhm @ Vgs 2.5V (drain pins 5-8 face the DRAIN bus, source 1-3 face the Minus bolt)
place('Package_SO', 'SOIC-8_3.9x4.9mm_P1.27mm', 'Q1', 'AO4402', 100.0, 0.0, 180,
      {'1': 'GND', '2': 'GND', '3': 'GND', '4': 'GATE', '5': 'DRAIN', '6': 'DRAIN', '7': 'DRAIN', '8': 'DRAIN'}, 'C115828')
place('Resistor_SMD', 'R_0805_2012Metric', 'R35', '510R', 104.5, -4.0, 180, {'1': 'DUMP', '2': 'GATE'}, 'C17734')
place('Resistor_SMD', 'R_0805_2012Metric', 'R36', '10K', 104.5, -6.5, 180, {'1': 'GND', '2': 'GATE'}, 'C17414')

# ------------------------------------------------------------ input (Plus side)
# F1: PTC 2920, 5A hold / 10A trip, 24V, 3mOhm (Littelfuse 2920L500/24SLDR)
place('Fuse', 'Fuse_2920_7451Metric', 'F1', '2920L500 5A', 13.5, -12.3, 0, {'1': 'BAT+', '2': 'VCC'}, 'C1512058')
place('Diode_SMD', 'D_SMB', 'D2', 'SMBJ5.0A', 20.0, -6.0, 0, {'1': 'VCC', '2': 'GND'}, 'C440263')

# ------------------------------------------------------------ quiet zone: MCU & analog
place('Package_SO', 'SOIC-14_3.9x8.7mm_P1.27mm', 'U2', 'ATTINY1624-SSU', 31.0, 3.0, 90,
      {'1': 'VCC', '3': 'VREF', '4': 'PA6', '5': 'PA7', '6': 'RXD0', '7': 'TXD0',
       '8': 'DUMP', '9': 'ENABLE', '10': 'RESET', '11': 'REF_EN', '13': 'PA3', '14': 'GND'}, 'C5160891')
place('Capacitor_SMD', 'C_0805_2012Metric', 'C1', '100nF', 25.0, 3.0, 90, {'1': 'VCC', '2': 'GND'}, 'C49678')
place('Capacitor_SMD', 'C_0805_2012Metric', 'C2', '10uF', 22.6, 3.0, 90, {'1': 'VCC', '2': 'GND'}, 'C15850')
place('Connector_PinSocket_2.54mm', 'PinSocket_1x03_P2.54mm_Vertical', 'UPDI1', 'UPDI', 26.0, -6.5, 90,
      {'1': 'VCC', '2': 'RESET', '3': 'GND'}, '', populate=False)
place('Package_TO_SOT_SMD', 'SOT-23', 'D1', 'AZ432ANTR-E1', 37.5, -6.0, 0, {'1': 'VREF', '2': 'VREF', '3': 'GND'}, 'C84139')
place('Resistor_SMD', 'R_0805_2012Metric', 'R2', '1K', 41.5, -6.0, 90, {'1': 'REF_EN', '2': 'VREF'}, 'C17513')
place('LED_SMD', 'LED_0603_1608Metric', 'D4', 'Blue', 18.0, 0.5, 180, {'1': 'LED_B', '2': 'PA6'}, 'C72043')
place('Resistor_SMD', 'R_0805_2012Metric', 'R34', '2K2', 18.0, 3.0, 0, {'1': 'GND', '2': 'LED_B'}, 'C17520')
place('Resistor_SMD', 'R_0805_2012Metric', 'R5', '180R', 38.0, 0.5, 0, {'1': 'OPTO_A', '2': 'TXD0'}, 'C25270')
place('Resistor_SMD', 'R_0805_2012Metric', 'R1', '100K', 38.0, 3.0, 180, {'1': 'VCC', '2': 'RESET'}, 'C149504')
place('Resistor_SMD', 'R_0805_2012Metric', 'R30', '2K2', 38.0, 5.5, 0, {'1': 'GND', '2': 'RXD0'}, 'C17520')
place('Resistor_SMD', 'R_0805_2012Metric', 'R31', '10K', 42.0, 1.5, 90, {'1': 'PA3', '2': 'GND'}, 'C17414')
# internal (board/load) temperature sensor at the edge of the quiet zone, next to the load block
place('Resistor_SMD', 'R_0805_2012Metric', 'R32', 'NTC 10K B3950', 46.0, -3.0, 90, {'1': 'ENABLE', '2': 'PA7'}, 'C51597')
place('Resistor_SMD', 'R_0805_2012Metric', 'R33', '10K', 46.0, 1.5, 90, {'1': 'PA7', '2': 'GND'}, 'C17414')
place('Package_SO', 'SOP-4_4.4x2.6mm_P1.27mm', 'U1', 'EL3H7(B)(TA)-G', 31.0, 11.5, 180,
      {'1': 'OPTO_A', '2': 'GND', '3': 'TXOUT1', '4': 'TXOUT2'}, 'C32565')
# comms: 1.25 mm "Mini Micro JST" = Molex PicoBlade compatible, SMD right angle, cable exits at the bottom edge
PB = 'Molex_PicoBlade_53261-0271_1x02-1MP_P1.25mm_Horizontal'
place('Connector_Molex', PB, 'TX1', 'TX', 22.0, 12.4, 0, {'1': 'TXOUT1', '2': 'TXOUT2'}, 'C177225')
place('Connector_Molex', PB, 'RX1', 'RX', 40.5, 12.4, 0, {'1': 'RXD0', '2': 'VCC'}, 'C177225')
# red "balancing" LED near the VCC bus
place('LED_SMD', 'LED_0805_2012Metric', 'D3', 'Red', 47.0, 12.5, 0, {'1': 'LED_R', '2': 'VCC'}, 'C84256')
place('Resistor_SMD', 'R_0805_2012Metric', 'R37', '2K2', 100.0, 12.0, 180, {'1': 'LED_R', '2': 'DRAIN'}, 'C17520')

# external/cell temperature: NTC R23 at the bottom board edge right next to the Plus bolt (cell terminal)
place('Resistor_SMD', 'R_0805_2012Metric', 'R23', 'NTC 10K B3950', 13.0, 14.3, 0, {'1': 'ENABLE', '2': 'PA3'}, 'C51597')
# R23B: assembly option (DNP) for the same sensor input, next to the load block. Fit either R23 or R23B.
place('Resistor_SMD', 'R_0805_2012Metric', 'R23B', 'NTC 10K B3950 DNP', 48.0, -7.0, 90, {'1': 'ENABLE', '2': 'PA3'}, 'C51597', populate=False)

place('', 'diybms_logo_24x10mm', 'G1', 'LOGO', 31.0, -3.0, 0, {}, '', populate=False,
      libpath='/home/claude/repo/ModuleV450/ModuleV450.pretty')
logo = [f for f in board.GetFootprints() if f.GetReference() == 'G1'][0]
logo.Flip(logo.GetPosition(), False)
logo.Reference().SetVisible(False); logo.Value().SetVisible(False)
logo.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_BOARD_ONLY)

# ------------------------------------------------------------ outline
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
# bolt pads
for L in (F, B):
    zone('BAT+', L, [(-BIG, -BIG), (9.0, -BIG), (9.0, BIG), (-BIG, BIG)], 3)
# bottom side: Plus-pole copper extended under R23 = thermal path from the cell terminal to the NTC
zone('BAT+', B, [(8.5, 11.2), (15.5, 11.2), (15.5, BIG), (8.5, BIG)], 3)
zone('BAT+', F, [(8.0, -15.4), (11.0, -15.4), (11.0, -9.6), (8.0, -9.6)], 3)          # tongue to F1 pad 1
zone('GND', F, [(114.5, -BIG), (PITCH + BIG, -BIG), (PITCH + BIG, BIG), (114.5, BIG)], 3)
# VCC: feed strip along the top edge + vertical bus left of the load block
zone('VCC', F, [(15.6, -15.4), (56.2, -15.4), (56.2, 13.8), (50.8, 13.8), (50.8, -9.4), (15.6, -9.4)], 2)
# series nodes between the resistors
for si, y in enumerate(ROWS, 1):
    for k in range(3):
        x0 = COLS[k] + 2.0
        zone('S%d_%d' % (si, k + 1), F, [(x0, y - 2.1), (x0 + 6.0, y - 2.1), (x0 + 6.0, y + 2.1), (x0, y + 2.1)], 2)
# DRAIN bus right of the load block + tongue to Q1 drain
zone('DRAIN', F, [(90.0, -13.8), (98.3, -13.8), (98.3, 13.8), (90.0, 13.8)], 2)
# load return: Q1 source -> Minus bolt, on top only
zone('GND', F, [(101.6, -1.25), (116.0, -1.25), (116.0, 10.0), (101.6, 10.0)], 2)
# bottom: GND plane (signal reference), star-connected at the Minus bolt; excludes the tab
zone('GND', B, [(9.6, -BIG), (PITCH + BIG, -BIG), (PITCH + BIG, BIG), (9.6, BIG)], 1, solid=False)

# ------------------------------------------------------------ pre-routed MCU supply branch (star at F1)
def track(netname, pts, w, layer=F):
    for a, b in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(board); t.SetStart(P(*a)); t.SetEnd(P(*b))
        t.SetWidth(MM(w)); t.SetLayer(layer); t.SetNet(net(netname)); t.SetLocked(True); board.Add(t)
track('VCC', [(16.89, -12.3), (16.89, -8.5), (17.85, -7.5), (17.85, -6.0)], 1.2)
# star branch: TVS -> C2 (10u) -> C1 (100n) -> U2 pin 1, nothing else taps the load strip for the MCU
track('VCC', [(17.85, -6.0), (17.85, -3.0), (20.5, -3.0), (20.5, 3.95), (22.6, 3.95)], 0.8)
track('VCC', [(22.6, 3.95), (25.0, 3.95)], 0.8)
track('VCC', [(25.0, 3.95), (25.9, 4.85), (26.6, 5.48), (27.19, 5.48)], 0.5)
track('GND', [(22.6, 2.05), (25.0, 2.05)], 0.8)
track('DRAIN', [(97.6, 12.0), (99.09, 12.0)], 0.8)
track('OPTO_A', [(37.09, 0.5), (36.0, 1.6), (36.0, 11.0), (35.0, 12.135), (34.19, 12.135)], 0.3)
track('VCC', [(38.91, 3.0), (40.3, 3.0), (40.3, 8.2), (41.12, 9.0), (41.12, 10.0)], 0.4)
track('GND', [(25.0, 2.05), (25.0, 1.2), (25.68, 0.52), (27.19, 0.52)], 0.5)

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
text('+', 6.0, -12.0, FS, 3.0, thick=0.4); text('-', 117.0, -12.0, FS, 3.0, thick=0.4)
text('+', 6.0, -12.0, BS, 3.0, True, 0.4); text('-', 117.0, -12.0, BS, 3.0, True, 0.4)
text('HOT!', 73.0, 0.0, FS, 1.2)
text('DIYBMS v4.5 cell module rev B', 73.0, -6.0, BS, 1.4, True, 0.22)
text('bolt-on, 123mm bolt spacing', 73.0, -3.0, BS, 1.1, True)
text('after BMS_alt v1.7 (Jau/Vas)', 73.0, -0.5, BS, 1.1, True)
text('load 4S4P 16x 1R2 = 1R2 (~3A)', 73.0, 2.0, BS, 1.1, True)
text('JLCJLCJLCJLC', 73.0, 5.0, BS, 1.0, True, 0.15)

out = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/work/out2/ModuleV450_Bolt123.kicad_pcb'
board.Save(out)
json.dump(BOM, open(out.replace('.kicad_pcb', '_bommap.json'), 'w'), indent=1)
print('saved', out, len(board.GetFootprints()), 'footprints', len(nets), 'nets')
