import ROOT, numpy as np, os, glob

def get_point(path):
    f = ROOT.TFile.Open(path)
    evt = f.Get("Event")
    nshow = evt.GetEntries()
    Eprim = np.zeros(1)
    evt.SetBranchAddress("Eprim", Eprim)
    evt.GetEntry(0)
    # sum muons over all data_1 cycles
    nmu_tot = 0
    ek_all = []
    for k in f.GetListOfKeys():
        if k.GetName() != "data_1":
            continue
        nt = f.Get("data_1;%d" % k.GetCycle())
        if not nt:
            continue
        id_v = np.zeros(1); ek_v = np.zeros(1)
        px=np.zeros(1); py=np.zeros(1); pz=np.zeros(1)
        nt.SetBranchAddress("id", id_v); nt.SetBranchAddress("ek", ek_v)
        nt.SetBranchAddress("px", px); nt.SetBranchAddress("py", py); nt.SetBranchAddress("pz", pz)
        n = nt.GetEntries()
        for i in range(n):
            nt.GetEntry(i)
            if id_v[0]!=5 and id_v[0]!=6: continue
            p = np.sqrt(px[0]**2+py[0]**2+pz[0]**2)
            th = np.degrees(np.arccos(min(1,max(-1,pz[0]/p)))) if p>0 else 90
            if th < 7.0:  # vertical window
                nmu_tot += 1
                ek_all.append(ek_v[0])
    f.Close()
    return float(Eprim[0]), nshow, nmu_tot, np.array(ek_all)

# print muon multiplicity (theta<7) per primary for a few energy points
print("E_prim  Nshow  Nmu(theta<7)  mu/shower  <ek>")
for p in ["out_0deg/DAT001005.root","out_0deg/DAT001008.root",
          "out_0deg/DAT001010.root","out_0deg/DAT001013.root",
          "out_0deg/DAT001015.root","out_0deg/DAT001020.root"]:
    E, ns, nmu, ek = get_point(p)
    print(f"{E:.3g}  {ns}  {nmu}  {nmu/ns:.3f}  {ek.mean() if len(ek) else 0:.2f}")
