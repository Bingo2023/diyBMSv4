import sys,pcbnew
OX,OY=60.0,100.0
b=pcbnew.LoadBoard(sys.argv[1])
P=lambda x,y: pcbnew.VECTOR2I(pcbnew.FromMM(OX+x),pcbnew.FromMM(OY+y))
POS={'U2':(21.0,8.3,0),'C1':(15.0,-0.4,0),'C2':(12.6,-0.4,0),'R23':(10.0,12.6,90),'R23B':(33.2,-9.6,0),
     'TX1':(15.8,8.0,0),'RX1':(28.5,8.0,0),'U1':(24.6,11.2,90),'UPDI1':(20.0,-5.0,0),'D4':(21.6,-8.8,0),'R34':(25.1,-8.8,0),
     'D1':(28.8,-9.2,0),'R2':(28.6,-2.6,0),'R5':(28.0,0.5,0),'R1':(28.0,3.0,0),'R30':(28.0,5.5,0),'R31':(31.0,1.5,90),'R32':(33.2,-2.6,90),'R33':(33.2,1.5,90),
     'Q1':(73.0,4.0,0),'R36':(79.6,-4.5,0),'R35':(79.6,-7.0,0),'R37':(72.9,12.5,90),'D3':(32.3,6.0,0),'F1':(13.5,-12.3,0),'D2':(16.0,-9.1,0)}
for f in b.GetFootprints():
    r=f.GetReference()
    if r in POS:
        x,y,a=POS[r]; t=f.Reference(); t.SetPosition(P(x,y)); t.SetTextAngleDegrees(a)
        t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8),pcbnew.FromMM(0.8))); t.SetTextThickness(pcbnew.FromMM(0.12))
# UPDI header GND pin: solid connection to the bottom GND plane (only one thermal spoke possible otherwise)
for f in b.GetFootprints():
    if f.GetReference() == 'UPDI1':
        for pd in f.Pads():
            if pd.GetNetname() == 'GND': pd.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
def _stub(t):   # short dangling VCC stub the router leaves inside the D2 pad
    if t.GetNetname() != 'VCC' or t.GetLength() >= pcbnew.FromMM(0.6): return False
    return any(abs(pcbnew.ToMM(pt.x) - OX - 13.85) < 0.05 and -5.5 < pcbnew.ToMM(pt.y) - OY < -4.0 for pt in (t.GetStart(), t.GetEnd()))
for t in list(b.GetTracks()):
    if t.GetClass() == 'PCB_TRACK' and not t.IsLocked() and (t.GetNetname() in ('GATE',) or t.GetLength() < pcbnew.FromMM(0.05) or _stub(t)):
        b.Remove(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save(sys.argv[2])
b = pcbnew.LoadBoard(sys.argv[2])
pcbnew.WriteDRCReport(b,sys.argv[3],pcbnew.EDA_UNITS_MILLIMETRES,True)
