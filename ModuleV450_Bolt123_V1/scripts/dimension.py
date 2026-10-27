#!/usr/bin/env python3
"""Draw a technical dimension (centre marks, extension lines, arrows, label) between two hole centres."""
import math
from PIL import Image, ImageDraw, ImageFont

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
SS = 4   # supersampling


def dimension(img, p1, p2, offset, label, color=(30, 30, 30), outline=None, width=3, font_px=34,
              hole_r=None):
    """p1, p2: hole centres (px). offset: signed distance of the dimension line from the axis p1-p2 (px)."""
    W, H = img.size
    big = Image.new('RGBA', (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    s = lambda p: (p[0] * SS, p[1] * SS)
    (x1, y1), (x2, y2) = p1, p2
    L = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / L, (y2 - y1) / L            # along
    nx, ny = -uy, ux                                  # normal
    q1 = (x1 + nx * offset, y1 + ny * offset)
    q2 = (x2 + nx * offset, y2 + ny * offset)
    sign = 1 if offset >= 0 else -1
    over = 12 * sign

    def strokes(col, wd):
        lw = int(wd * SS)
        # centre marks
        r = 14
        for (cx, cy) in (p1, p2):
            d.line([s((cx - r * ux, cy - r * uy)), s((cx + r * ux, cy + r * uy))], fill=col, width=lw)
            d.line([s((cx - r * nx, cy - r * ny)), s((cx + r * nx, cy + r * ny))], fill=col, width=lw)
        # extension lines (dashed) from the hole centre to just beyond the dimension line
        start = 18
        for (cx, cy) in (p1, p2):
            a = (cx + nx * start * sign, cy + ny * start * sign)
            b = (cx + nx * (offset + over), cy + ny * (offset + over))
            seg = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(seg // 14))
            for k in range(n):
                t0, t1 = k / n, (k + 0.6) / n
                d.line([s((a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)),
                        s((a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1))], fill=col, width=lw)
        # dimension line between the arrow tips
        AL, AW = 26, 9
        d.line([s((q1[0] + ux * AL * 0.8, q1[1] + uy * AL * 0.8)),
                s((q2[0] - ux * AL * 0.8, q2[1] - uy * AL * 0.8))], fill=col, width=lw)
        # arrow heads (filled)
        for tip, dirn in ((q1, 1), (q2, -1)):
            bx, by = tip[0] + ux * AL * dirn, tip[1] + uy * AL * dirn
            d.polygon([s(tip), s((bx + nx * AW, by + ny * AW)), s((bx - nx * AW, by - ny * AW))], fill=col)

    if outline:
        strokes(outline + (255,), width + 3)
    strokes(color + (255,), width)

    # label in a rounded box at the middle of the dimension line
    font = ImageFont.truetype(FONT, font_px * SS)
    tb = d.textbbox((0, 0), label, font=font)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    mx, my = (q1[0] + q2[0]) / 2 * SS, (q1[1] + q2[1]) / 2 * SS
    pad = 10 * SS
    box = [mx - tw / 2 - pad, my - th / 2 - pad, mx + tw / 2 + pad, my + th / 2 + pad]
    d.rounded_rectangle(box, radius=8 * SS, fill=(255, 255, 255, 235), outline=(color + (255,)), width=2 * SS)
    d.text((mx - tw / 2 - tb[0], my - th / 2 - tb[1]), label, font=font, fill=color + (255,))

    small = big.resize((W, H), Image.LANCZOS)
    out = img.convert('RGBA')
    out.alpha_composite(small)
    return out.convert('RGB')


def annotate_render(src, dst, pitch_mm, side='top', dpi=300, margin_mm=1.0, half_mm=15.75, pad_top=110):
    """Preview render (from render_preview.py): add white space above and dimension the bolt spacing."""
    im = Image.open(src).convert('RGB')
    W, H = im.size
    s = dpi / 25.4
    xa = (half_mm + margin_mm) * s
    xb = (half_mm + margin_mm + pitch_mm) * s
    if side == 'bottom':
        xa, xb = W - xb, W - xa
    yc = (half_mm + margin_mm) * s + pad_top
    canvas = Image.new('RGB', (W, H + pad_top), (255, 255, 255))
    canvas.paste(im, (0, pad_top))
    out = dimension(canvas, (xa, yc), (xb, yc), -(yc - 48), '%g mm' % pitch_mm)
    out.save(dst)


if __name__ == '__main__':
    import sys
    mode = sys.argv[1]
    if mode == 'render':
        annotate_render(sys.argv[2], sys.argv[3], float(sys.argv[4]), sys.argv[5])
    elif mode == 'photo':
        src, dst, x1, y1, x2, y2, off, label = sys.argv[2:10]
        im = Image.open(src).convert('RGB')
        out = dimension(im, (float(x1), float(y1)), (float(x2), float(y2)), float(off), label,
                        color=(20, 20, 20), outline=(255, 255, 255), width=3, font_px=30)
        out.save(dst, quality=90)
