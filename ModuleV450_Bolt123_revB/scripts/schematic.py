#!/usr/bin/env python3
"""Schematic of ModuleV450 Bolt123 Rev B (drawn from the routed board's netlist)."""
import sys
import schemdraw
import schemdraw.elements as elm

schemdraw.config(fontsize=10, lw=1.1)
elm.style(elm.STYLE_IEC)

OUT = sys.argv[1] if len(sys.argv) > 1 else 'schematic'
d = schemdraw.Drawing(show=False)
d.config(unit=2.0)

def tag(at, name, side='right', color='#1a4fa0'):
    """Net label (like a KiCad global label)."""
    t = elm.Tag(width=0.25 * len(name) + 0.4).at(at).label(name, fontsize=9, color=color)
    t = t.right() if side == 'right' else t.left()
    d.add(t.color(color))

def vcc(at):
    d.add(elm.Vdd().at(at).label('VCC', fontsize=9))

def gnd(at):
    d.add(elm.Ground().at(at))

def frame(x0, y0, x1, y1, title):
    d.add(elm.Line().at((x0, y0)).to((x1, y0)).color('#999999').linestyle('--'))
    d.add(elm.Line().at((x1, y0)).to((x1, y1)).color('#999999').linestyle('--'))
    d.add(elm.Line().at((x1, y1)).to((x0, y1)).color('#999999').linestyle('--'))
    d.add(elm.Line().at((x0, y1)).to((x0, y0)).color('#999999').linestyle('--'))
    d.add(elm.Label().at((x0 + 0.3, y1 - 0.45)).label(title, fontsize=11, halign='left', color='#444444'))

def conn(x, y, title, pins):
    """Simple connector box, pins listed top->bottom, pin stubs to the left. Returns pin end points."""
    h = 0.8 * len(pins) + 0.4
    d.add(elm.Line().at((x, y + 0.4)).to((x + 1.0, y + 0.4)))
    d.add(elm.Line().at((x + 1.0, y + 0.4)).to((x + 1.0, y + 0.4 - h)))
    d.add(elm.Line().at((x + 1.0, y + 0.4 - h)).to((x, y + 0.4 - h)))
    d.add(elm.Line().at((x, y + 0.4 - h)).to((x, y + 0.4)))
    d.add(elm.Label().at((x + 0.5, y + 0.9)).label(title, fontsize=9))
    ends = []
    for i, nm in enumerate(pins):
        py = y - 0.8 * i
        d.add(elm.Dot(open=True).at((x, py)))
        d.add(elm.Label().at((x + 0.5, py)).label(str(i + 1), fontsize=8))
        d.add(elm.Label().at((x + 1.2, py)).label(nm, fontsize=8, halign='left'))
        ends.append((x, py))
    return ends

# ===================================================== 1) input / supply
frame(-1, 0, 19, 12, '1  Zellanschluss, Sicherung, MCU-Versorgung (Sternpunkt an F1)')
d.add(elm.Dot(open=True).at((0.5, 9)).label('BAT+\nPlus-Bolzen', loc='bottom', fontsize=9))
f1 = d.add(elm.Fuse().at((0.5, 9)).right().length(4)
           .label('F1\n2920L500/24SLDR\n5 A / 10 A, 3 mΩ', loc='top', fontsize=9))
d.add(elm.Line().right().length(1.5))
d.add(elm.Dot())
p_star = d.here
d.add(elm.Line().right().length(2.0))
d.add(elm.Line().up().length(1.5))
d.add(elm.Line().right().length(1.5))
tag(d.here, 'VCC (Last)')
d.add(elm.Label().at((11.5, 10.0)).label('→ Kupferfläche zum Lastblock', fontsize=8, color='#666666', halign='left'))
# MCU branch
d.add(elm.Line().at(p_star).down().length(1.0))
d.add(elm.Dot()); p1 = d.here
d.add(elm.DiodeTVS().at(p1).down().length(3).reverse().label('D2\nSMBJ5.0A', loc='bottom', fontsize=9))
gnd(d.here)
d.add(elm.Line().at(p1).right().length(3))
d.add(elm.Dot()); p2 = d.here
d.add(elm.Capacitor().at(p2).down().length(3).label('C2\n10 µF', loc='bottom', fontsize=9))
gnd(d.here)
d.add(elm.Line().at(p2).right().length(3))
d.add(elm.Dot()); p3 = d.here
d.add(elm.Capacitor().at(p3).down().length(3).label('C1\n100 nF', loc='bottom', fontsize=9))
gnd(d.here)
d.add(elm.Line().at(p3).right().length(2.5))
tag(d.here, 'VCC (U2 Pin 1)')
d.add(elm.Dot(open=True).at((0.5, 2.5)).label('BAT−  Minus-Bolzen\n(Sternpunkt GND)', loc='top', fontsize=9))
d.add(elm.Line().at((0.5, 2.5)).right().length(1.5))
gnd(d.here)

# ===================================================== 2) MCU
frame(20, 0, 44, 12, '2  Mikrocontroller ATtiny1624-SSU (U2)')
ic = elm.Ic(pins=[
    elm.IcPin(name='VCC', pin='1', side='L'),
    elm.IcPin(name='PA0/RESET/UPDI', pin='10', side='L'),
    elm.IcPin(name='PA1', pin='11', side='L'),
    elm.IcPin(name='PA5', pin='3', side='L'),
    elm.IcPin(name='PA6', pin='4', side='L'),
    elm.IcPin(name='PA7', pin='5', side='L'),
    elm.IcPin(name='PA2', pin='12', side='L'),
    elm.IcPin(name='PB0', pin='9', side='R'),
    elm.IcPin(name='PB1', pin='8', side='R'),
    elm.IcPin(name='PB2/TXD', pin='7', side='R'),
    elm.IcPin(name='PB3/RXD', pin='6', side='R'),
    elm.IcPin(name='PA3', pin='13', side='R'),
    elm.IcPin(name='PA4', pin='2', side='R'),
    elm.IcPin(name='GND', pin='14', side='B'),
], size=(5, 8.0), pinspacing=1.1, leadlen=1.2).right().at((29.5, 1.8)).label('U2\nATtiny1624', loc='top', fontsize=10)
u2 = d.add(ic)
left = [('VCC', 'VCC'), ('PA0/RESET/UPDI', 'RESET'), ('PA1', 'REF_EN'), ('PA5', 'VREF'),
        ('PA6', 'PA6'), ('PA7', 'PA7'), ('PA2', None)]
right = [('PB0', 'ENABLE'), ('PB1', 'DUMP'), ('PB2/TXD', 'TXD0'), ('PB3/RXD', 'RXD0'), ('PA3', 'PA3'), ('PA4', None)]
for pin, net in left:
    a = getattr(u2, pin.replace('/', '_')) if hasattr(u2, pin.replace('/', '_')) else u2.absanchors[pin]
    if net:
        tag(a, net, side='left')
    else:
        d.add(elm.Label().at(a).label('n.c.', loc='left', fontsize=8, halign='right'))
for pin, net in right:
    a = u2.absanchors[pin]
    if net:
        tag(a, net)
    else:
        d.add(elm.Label().at(a).label('  n.c.', fontsize=8, halign='left'))
gnd(u2.absanchors['GND'])

# ===================================================== 3) reference + temperature sensors
frame(45, 0, 73, 12, '3  Spannungsreferenz und Temperatursensoren')
# reference
tag((46.5, 10), 'REF_EN', side='L')
d.add(elm.Line().at((46.5, 10)).right().length(0.5))
d.add(elm.Resistor().right().length(2.5).label('R2\n1 kΩ', fontsize=9))
d.add(elm.Dot()); pv = d.here
d.add(elm.Line().right().length(1)); tag(d.here, 'VREF')
d.add(elm.Zener().at(pv).down().length(3).reverse().label('D1  AZ432\n1,25 V ±0,5 %', loc='bottom', fontsize=9))
gnd(d.here)
# internal temp
x = 57.5
tag((x, 10.5), 'ENABLE', side='L')
d.add(elm.Line().at((x, 10.5)).right().length(0.6))
d.add(elm.Line().down().length(0.5))
d.add(elm.Thermistor().down().length(2.5).label('R32  NTC 10k\nB3950\n(Platine)', loc='bottom', fontsize=8))
d.add(elm.Dot()); pt = d.here
d.add(elm.Line().right().length(0.8)); tag(d.here, 'PA7')
d.add(elm.Resistor().at(pt).down().length(2.5).label('R33\n10 kΩ', loc='bottom', fontsize=9))
gnd(d.here)
# external temp
x = 64.5
tag((x, 10.5), 'ENABLE', side='L')
d.add(elm.Line().at((x, 10.5)).right().length(0.6))
d.add(elm.Line().down().length(0.5))
d.add(elm.Thermistor().down().length(2.5).label('R23  NTC 10k\n(Zellpol, Rand)', loc='bottom', fontsize=8))
d.add(elm.Dot()); pe = d.here
d.add(elm.Line().right().length(0.8)); tag(d.here, 'PA3')
d.add(elm.Resistor().at(pe).down().length(2.5).label('R31\n10 kΩ', loc='bottom', fontsize=9))
gnd(d.here)
# R23B: assembly option parallel to R23
d.add(elm.Dot().at((65.1, 10.0)))
d.add(elm.Line().at((65.1, 10.0)).right().length(3.0))
d.add(elm.Thermistor().down().length(2.5).label('R23B  NTC 10k\nBestückoption\n(am Lastblock, DNP)', loc='bottom', fontsize=8))
d.add(elm.Line().down().length(0.5))
d.add(elm.Line().left().length(3.0))
d.add(elm.Dot())
d.add(elm.Label().at((53.8, 1.3)).label(
    'R23 sitzt an der Unterkante direkt neben dem Plus-Bolzen. Darunter (Unterseite) eine Kupferfläche\n'
    'am Plus-Pol als Wärmebrücke → R23 misst die Polbolzen- bzw. Zelltemperatur.\n'
    'R23B = alternative Position am Lastblock (nicht bestückt). Nur R23 ODER R23B bestücken.',
    fontsize=8, halign='left', color='#666666'))

# ===================================================== 4) reset / UPDI / blue LED
frame(-1, -13, 19, -1, '4  Reset, Programmierung (UPDI), Status-LED')
vcc((1.5, -3.5))
d.add(elm.Resistor().at((1.5, -3.5)).down().length(2.5).label('R1\n100 kΩ', fontsize=9))
d.add(elm.Dot()); pr = d.here
d.add(elm.Line().right().length(1)); tag(d.here, 'RESET')
up = conn(6.0, -7.5, 'UPDI1 (optional)', ['VCC', 'RESET/UPDI', 'GND'])
for (px, py), nm in zip(up, ['VCC', 'RESET', None]):
    d.add(elm.Line().at((px, py)).left().length(1.0))
    if nm: tag(d.here, nm, side='left')
    else: gnd(d.here)
tag((12, -5), 'PA6', side='L')
d.add(elm.Line().at((12, -5)).right().length(0.6))
d.add(elm.Line().down().length(0.5))
d.add(elm.LED().down().length(2.5).label('D4\nblau', loc='bottom', fontsize=9))
d.add(elm.Resistor().down().length(2.5).label('R34\n2,2 kΩ', loc='bottom', fontsize=9))
gnd(d.here)

# ===================================================== 5) comms
frame(20, -13, 44, -1, '5  Kommunikation (isoliert), Stecker Molex PicoBlade 1,25 mm')
tag((21, -4), 'TXD0', side='L')
d.add(elm.Line().at((21, -4)).right().length(0.5))
d.add(elm.Resistor().right().length(2.5).label('R5\n180 Ω', fontsize=9))
p_r5 = d.here
opto = d.add(elm.Optocoupler().anchor('anode').at((26.5, -4)).label('U1\nEL3H7', loc='top', fontsize=9))
d.add(elm.Line().at(p_r5).to(opto.anode))
d.add(elm.Line().at(opto.cathode).down().length(0.6)); gnd(d.here)
d.add(elm.Line().at(opto.collector).right().length(2.5)); tc = d.here
d.add(elm.Line().at(opto.emitter).right().length(2.5)); te = d.here
txp = conn(36.0, -3.6, 'TX1  Molex 53261-0271', ['TXOUT1', 'TXOUT2'])
d.add(elm.Line().at(te).to((te[0], txp[0][1]))); d.add(elm.Line().to(txp[0]))
d.add(elm.Line().at(tc).to((tc[0] + 1.0, tc[1]))); d.add(elm.Line().to((tc[0] + 1.0, txp[1][1]))); d.add(elm.Line().to(txp[1]))
d.add(elm.Label().at((30.0, -7.0)).label('Pin 1 = Emitter, Pin 2 = Kollektor\n→ zum RX des nächsten Moduls', fontsize=8, color='#666666', halign='left'))
rxp = conn(26.5, -8.5, 'RX1  Molex 53261-0271', ['RXD0', 'VCC'])
d.add(elm.Line().at(rxp[0]).left().length(3.2))
d.add(elm.Dot()); prx = d.here
d.add(elm.Line().left().length(0.3)); tag(d.here, 'RXD0', side='left')
d.add(elm.Resistor().at(prx).down().length(2.2).label('R30\n2,2 kΩ', loc='bottom', fontsize=9))
gnd(d.here)
d.add(elm.Line().at(rxp[1]).left().length(0.5)); tag(d.here, 'VCC', side='left')
d.add(elm.Label().at((29.0, -11.2)).label('RX Pin 2 (VCC) speist den Optokoppler-\nTransistor des vorherigen Moduls', fontsize=8, color='#666666', halign='left'))

# ===================================================== 6) balancing load
frame(45, -13, 73, -1, '6  Balancing-Last 16 × 1,2 Ω 2512 (4S4P = 1,2 Ω, ca. 3 A @ 3,65 V)')
xs = 47.0
vcc((xs, -2.8))
d.add(elm.Line().at((xs, -2.8)).down().length(0.4))
top = d.here
ybase = top[1]
rows_y = [ybase, ybase - 1.6, ybase - 3.2, ybase - 4.8]
names = [['R6', 'R7', 'R8', 'R9'], ['R10', 'R11', 'R12', 'R13'], ['R14', 'R15', 'R16', 'R17'], ['R18', 'R19', 'R20', 'R21']]
d.add(elm.Line().at((xs, ybase)).to((xs, rows_y[-1])))
xend = None
for y, nm in zip(rows_y, names):
    d.add(elm.Dot().at((xs, y)))
    d.add(elm.Line().at((xs, y)).right().length(0.3))
    for r in nm:
        d.add(elm.Resistor().right().length(2.0).label(r, fontsize=8))
    d.add(elm.Line().right().length(0.3))
    xend = d.here[0]
    d.add(elm.Dot())
d.add(elm.Line().at((xend, ybase)).to((xend, rows_y[-1])))
d.add(elm.Line().at((xend, ybase)).right().length(1.0))
d.add(elm.Dot()); pdrain = d.here
d.add(elm.Line().right().length(0.4)); tag(d.here, 'DRAIN')
d.add(elm.Label().at((xs + 0.4, rows_y[-1] - 0.8)).label('alle 1,2 Ω 1 % 1 W (UniOhm 25121WF120KT4E, C46193)', fontsize=8, halign='left', color='#666666'))
# MOSFET
qx, qy = 64.0, -6.0
q1 = d.add(elm.NFet().right().reverse().at((qx, qy)).label('Q1  AO4402\nSO-8 20 V\n7 mΩ @2,5 V', loc='right', fontsize=9))
d.add(elm.Line().at(q1.drain).up().length(0.6)); tag(d.here, 'DRAIN', side='right')
d.add(elm.Line().at(q1.source).down().length(0.6)); gnd(d.here)
d.add(elm.Line().at(q1.gate).left().length(0.8))
d.add(elm.Dot()); pg = d.here
d.add(elm.Resistor().left().length(2.4).label('R35\n510 Ω', fontsize=9))
tag(d.here, 'DUMP', side='left')
d.add(elm.Resistor().at(pg).down().length(2.2).label('R36\n10 kΩ', loc='bottom', fontsize=9))
gnd(d.here)
# red LED
vcc((67.5, -2.8))
d.add(elm.LED().at((67.5, -2.8)).down().length(2.2).label('D3 rot', loc='bottom', fontsize=9))
d.add(elm.Resistor().down().length(2.2).label('R37\n2,2 kΩ', loc='bottom', fontsize=9))
tag(d.here, 'DRAIN', side='right')

# ===================================================== title block
d.add(elm.Label().at((45.3, -14.1)).label(
    'DIYBMS v4.5 Zellmodul – Bolt-on 123 mm, Rev B  ·  ATtiny1624  ·  Platine 154,5 × 31,5 mm  ·  2026-10-08',
    fontsize=10, halign='left'))
d.add(elm.Label().at((-1, -14.1)).label(
    'Netznamen (blau) verbinden gleichnamige Punkte. GND-Fläche unten nur am Minus-Bolzen mit dem Laststrompfad verbunden.',
    fontsize=8, halign='left', color='#666666'))

d.save(OUT + '.svg')
d.save(OUT + '.pdf')
d.save(OUT + '.png', dpi=110)
print('ok')
