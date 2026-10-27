#!/usr/bin/env python3
"""JLCPCB BOM + CPL from the routed board (rotation offsets as used for the original V450 CPL)."""
import sys, csv, json, re, collections
import pcbnew

board_file, bommap, outdir = sys.argv[1:4]
PFX = sys.argv[4] if len(sys.argv) > 4 else 'ModuleV450_Bolt123'
b = pcbnew.LoadBoard(board_file)
meta = json.load(open(bommap))
# footprint -> JLC rotation correction (derived from ModuleV450 KiCad vs. its JLC CPL)
ROT = [(r'^SOT-23', 180), (r'^SOIC-', 270), (r'^D_SMB', 0), (r'^SOP-4', 180),
       (r'^Molex_PicoBlade_53261', 180)]   # JLC model is 180 deg off vs. KiCad (checked in JLC viewer)

groups = collections.OrderedDict()
cpl = []
# panel support: several footprints with the same reference -> designators REF_1..REF_N (top to bottom)
_inst = collections.defaultdict(list)
for f in b.GetFootprints():
    _inst[f.GetReference()].append(f)
DESIG = {}
for r, fs in _inst.items():
    if len(fs) == 1:
        DESIG[fs[0].m_Uuid.AsString()] = r
    else:
        for i, f in enumerate(sorted(fs, key=lambda f: f.GetPosition().y), 1):
            DESIG[f.m_Uuid.AsString()] = '%s_%d' % (r, i)
for f in sorted(b.GetFootprints(), key=lambda f: (re.sub(r'\d', '', f.GetReference()), int(re.sub(r'\D', '', f.GetReference()) or 0), f.GetPosition().y)):
    base = f.GetReference()
    ref = DESIG[f.m_Uuid.AsString()]
    if base not in meta:
        continue
    value, lcsc, populate, fp = meta[base]
    if not populate or not lcsc:
        continue
    key = (value, fp, lcsc)
    groups.setdefault(key, []).append(ref)
    rot = f.GetOrientationDegrees()
    for pat, off in ROT:
        if re.match(pat, fp):
            rot += off
    rot %= 360
    # JLC places parts by their centre: use the centre of the copper pads (KiCad origin can differ, e.g. PicoBlade)
    pads = [p for p in f.Pads() if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH]
    bb = pads[0].GetBoundingBox()
    for p in pads[1:]: bb.Merge(p.GetBoundingBox())
    cx, cy = (bb.GetLeft() + bb.GetRight()) / 2, (bb.GetTop() + bb.GetBottom()) / 2
    cpl.append([ref, '%.4f' % pcbnew.ToMM(int(cx)), '%.4f' % -pcbnew.ToMM(int(cy)), 'top', '%.1f' % rot])

with open(outdir + '/' + PFX + '_bom_jlc.csv', 'w', newline='') as fh:
    w = csv.writer(fh, quoting=csv.QUOTE_ALL)
    w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
    for (value, fp, lcsc), refs in groups.items():
        w.writerow([value, ','.join(refs), fp, lcsc])
with open(outdir + '/' + PFX + '_cpl_jlc.csv', 'w', newline='') as fh:
    w = csv.writer(fh, quoting=csv.QUOTE_MINIMAL)
    w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    w.writerows(cpl)
# full BOM incl. hand-soldered parts
with open(outdir + '/' + PFX + '_bom_full.csv', 'w', newline='') as fh:
    w = csv.writer(fh, quoting=csv.QUOTE_ALL)
    w.writerow(['Designator', 'Value', 'Footprint', 'LCSC', 'Assembly'])
    for ref, (value, lcsc, populate, fp) in sorted(meta.items()):
        if ref == 'G1':
            continue
        w.writerow([ref, value, fp, lcsc, 'JLC SMT' if (populate and lcsc) else 'hand / optional'])
print(len(cpl), 'placements,', len(groups), 'BOM lines')
