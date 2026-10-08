#!/usr/bin/env python3
"""JLCPCB BOM + CPL from the routed board (rotation offsets as used for the original V450 CPL)."""
import sys, csv, json, re, collections
import pcbnew

board_file, bommap, outdir = sys.argv[1:4]
b = pcbnew.LoadBoard(board_file)
meta = json.load(open(bommap))
# footprint -> JLC rotation correction (derived from ModuleV450 KiCad vs. its JLC CPL)
ROT = [(r'^SOT-23', 180), (r'^SOIC-', 270), (r'^D_SMB', 180), (r'^SOP-4', 0)]

groups = collections.OrderedDict()
cpl = []
for f in sorted(b.GetFootprints(), key=lambda f: (re.sub(r'\d', '', f.GetReference()), int(re.sub(r'\D', '', f.GetReference()) or 0))):
    ref = f.GetReference()
    if ref not in meta:
        continue
    value, lcsc, populate, fp = meta[ref]
    if not populate or not lcsc:
        continue
    key = (value, fp, lcsc)
    groups.setdefault(key, []).append(ref)
    rot = f.GetOrientationDegrees()
    for pat, off in ROT:
        if re.match(pat, fp):
            rot += off
    rot %= 360
    pos = f.GetPosition()
    cpl.append([ref, '%.4f' % pcbnew.ToMM(pos.x), '%.4f' % -pcbnew.ToMM(pos.y), 'top', '%.1f' % rot])

with open(outdir + '/ModuleV450_Bolt123_bom_jlc.csv', 'w', newline='') as fh:
    w = csv.writer(fh, quoting=csv.QUOTE_ALL)
    w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
    for (value, fp, lcsc), refs in groups.items():
        w.writerow([value, ','.join(refs), fp, lcsc])
with open(outdir + '/ModuleV450_Bolt123_cpl_jlc.csv', 'w', newline='') as fh:
    w = csv.writer(fh, quoting=csv.QUOTE_MINIMAL)
    w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    w.writerows(cpl)
# full BOM incl. hand-soldered parts
with open(outdir + '/ModuleV450_Bolt123_bom_full.csv', 'w', newline='') as fh:
    w = csv.writer(fh, quoting=csv.QUOTE_ALL)
    w.writerow(['Designator', 'Value', 'Footprint', 'LCSC', 'Assembly'])
    for ref, (value, lcsc, populate, fp) in sorted(meta.items()):
        if ref == 'G1':
            continue
        w.writerow([ref, value, fp, lcsc, 'JLC SMT' if (populate and lcsc) else 'hand / optional'])
print(len(cpl), 'placements,', len(groups), 'BOM lines')
