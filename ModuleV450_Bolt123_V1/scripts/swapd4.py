import pcbnew, sys
src, dst = sys.argv[1:3]
b = pcbnew.LoadBoard(src)
old = b.FindFootprintByReference('D4')
pos, rot = old.GetPosition(), old.GetOrientation()
nets = {p.GetNumber(): p.GetNet() for p in old.Pads()}
txt = {'ref': (old.Reference().GetPosition(), old.Reference().GetTextAngle(), old.Reference().IsVisible())}
lib = '/usr/share/kicad/footprints/LED_SMD.pretty'
f = pcbnew.FootprintLoad(lib, 'LED_0805_2012Metric')
f.SetReference('D4'); f.SetValue('Yellow')
f.SetPosition(pos); f.SetOrientation(rot)
for p in f.Pads(): p.SetNet(nets[p.GetNumber()])
for k in ('LCSC', 'JLC'):
    pass
b.Remove(old); b.Add(f)
f.Reference().SetPosition(txt['ref'][0]); f.Reference().SetTextAngle(txt['ref'][1])
for p in f.Pads(): print(p.GetNumber(), p.GetNetname(), pcbnew.ToMM(p.GetPosition()))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(dst)
pcbnew.WriteDRCReport(b, dst.replace('.kicad_pcb','_drc.txt'), pcbnew.EDA_UNITS_MILLIMETRES, True)
