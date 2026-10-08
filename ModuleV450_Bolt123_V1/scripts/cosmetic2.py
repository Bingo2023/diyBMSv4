import sys,pcbnew
OX,OY=60.0,100.0
b=pcbnew.LoadBoard(sys.argv[1])
P=lambda x,y: pcbnew.VECTOR2I(pcbnew.FromMM(OX+x),pcbnew.FromMM(OY+y))
POS={'D4':(15.6,0.5,0),'R34':(15.6,3.0,0),'C1':(24.6,-1.3,0),'C2':(21.6,-1.3,0),'U2':(31.0,8.0,0),
     'R30':(38.0,7.1,0),'R23':(13.0,12.6,0),'R23B':(48.0,-9.0,0),'TX1':(22.0,8.0,0),'RX1':(40.5,8.0,0),'U1':(31.0,14.3,0),'R1':(38.0,1.75,0),'UPDI1':(34.0,-6.5,0),'R36':(107.4,-6.5,0),'R35':(107.4,-4.0,0)}
for f in b.GetFootprints():
    r=f.GetReference()
    if r in POS:
        x,y,a=POS[r]; t=f.Reference(); t.SetPosition(P(x,y)); t.SetTextAngleDegrees(a)
        t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8),pcbnew.FromMM(0.8))); t.SetTextThickness(pcbnew.FromMM(0.12))
for t in list(b.GetTracks()):   # router leaves short duplicate stubs on the pre-routed OPTO_A line
    if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'OPTO_A' and not t.IsLocked():
        b.Remove(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(sys.argv[2])
b = pcbnew.LoadBoard(sys.argv[2])
pcbnew.WriteDRCReport(b,sys.argv[3],pcbnew.EDA_UNITS_MILLIMETRES,True)
