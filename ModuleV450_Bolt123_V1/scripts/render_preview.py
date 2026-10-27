#!/usr/bin/env python3
"""Realistic PCB preview (green mask, HASL pads, white silk) composited from the Gerbers.
usage: render_preview.py board.kicad_pcb gerber_dir prefix out_top.png out_bottom.png [dpi]"""
import sys, os, subprocess, tempfile
import pcbnew
from PIL import Image, ImageDraw, ImageChops, ImageFilter

pcb, gdir, pfx, out_top, out_bot = sys.argv[1:6]
DPI = int(sys.argv[6]) if len(sys.argv) > 6 else 600
b = pcbnew.LoadBoard(pcb)
bb = b.GetBoardEdgesBoundingBox()
M = 1.0                                         # margin mm
x0, y0 = pcbnew.ToMM(bb.GetX()) - M, pcbnew.ToMM(bb.GetY()) - M
w, h = pcbnew.ToMM(bb.GetWidth()) + 2 * M, pcbnew.ToMM(bb.GetHeight()) + 2 * M
S = DPI / 25.4
W, H = int(round(w * S)), int(round(h * S))
tmp = tempfile.mkdtemp()

def layer(name):
    """render one gerber/drill file as white-on-black mask of exactly W x H pixels"""
    f = os.path.join(gdir, '%s-%s' % (pfx, name))
    if not os.path.exists(f):
        return Image.new('L', (W, H), 0)
    o = os.path.join(tmp, name + '.png')
    subprocess.run(['gerbv', '-x', 'png', '-o', o, '-D', str(DPI), '-B', '0',
                    '-O', '%.6fx%.6f' % (x0 / 25.4, -(y0 + h) / 25.4),
                    '-W', '%.6fx%.6f' % (w / 25.4, h / 25.4),
                    '-b', '#000000', '-f', '#ffffffff', f], check=True, capture_output=True)
    im = Image.open(o).convert('L')
    if im.size != (W, H):
        im = im.resize((W, H))
    return im.point(lambda v: 255 if v > 100 else 0)

# board shape from KiCad outline
sps = pcbnew.SHAPE_POLY_SET(); b.GetBoardPolygonOutlines(sps)
shape = Image.new('L', (W, H), 0)
d = ImageDraw.Draw(shape)
for i in range(sps.OutlineCount()):
    o = sps.Outline(i)
    d.polygon([((pcbnew.ToMM(o.CPoint(k).x) - x0) * S, (pcbnew.ToMM(o.CPoint(k).y) - y0) * S)
               for k in range(o.PointCount())], fill=255)
    for hi in range(sps.HoleCount(i)):
        hh = sps.CHole(i, hi)
        d.polygon([((pcbnew.ToMM(hh.CPoint(k).x) - x0) * S, (pcbnew.ToMM(hh.CPoint(k).y) - y0) * S)
                   for k in range(hh.PointCount())], fill=0)
drill = ImageChops.lighter(layer('PTH.drl'), layer('NPTH.drl'))

def compose(side):
    cu, mask, silk = (layer('F_Cu.gtl'), layer('F_Mask.gts'), layer('F_Silkscreen.gto')) if side == 'top' else \
                     (layer('B_Cu.gbl'), layer('B_Mask.gbs'), layer('B_Silkscreen.gbo'))
    img = Image.new('RGB', (W, H), (255, 255, 255))
    def paint(m, col):
        img.paste(Image.new('RGB', (W, H), col), (0, 0), m)
    inside = shape
    paint(inside, (16, 92, 52))                                   # substrate under mask
    under = ImageChops.multiply(cu, ImageChops.invert(mask))
    paint(ImageChops.multiply(under, inside), (34, 128, 70))      # copper under mask (lighter green)
    opening = ImageChops.multiply(mask, inside)
    paint(ImageChops.multiply(opening, ImageChops.invert(cu)), (196, 178, 128))   # bare FR4 in mask openings
    paint(ImageChops.multiply(opening, cu), (205, 205, 200))       # HASL pads
    silk_ok = ImageChops.multiply(ImageChops.multiply(silk, ImageChops.invert(mask)), inside)
    paint(silk_ok, (245, 245, 240))
    paint(ImageChops.multiply(drill, inside), (40, 40, 40))        # holes
    # thin dark edge
    edge = shape.filter(ImageFilter.FIND_EDGES)
    paint(edge, (10, 50, 28))
    if side == 'bottom':
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    # downscale for antialiasing
    return img.resize((W // 2, H // 2), Image.LANCZOS)

compose('top').save(out_top)
compose('bottom').save(out_bot)
print('ok', out_top, out_bot, W // 2, H // 2)
