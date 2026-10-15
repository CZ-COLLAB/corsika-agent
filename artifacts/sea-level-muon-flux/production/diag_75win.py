import ROOT, numpy as np, glob, os

def muons(path, tmin, tmax):
    f = ROOT.TFile.Open(path)
    evt = f.Get("Event")
    nshow = evt.GetEntries()
    nmu_all = 0
    nmu_win = 0
    eks_win = []
    for k in f.GetListOfKeys():
        if k.GetName() != "data_1": continue
        nt = f.Get("data_1;%d" % k.GetCycle())
        if not nt: continue
        id_v=np.zeros(1); ek_v=np.zeros(1); px=np.zeros(1); py=np.zeros(1); pz=np.zeros(1)
        nt.SetBranchAddress("id",id_v); nt.SetBranchAddress("ek",ek_v)
        nt.SetBranchAddress("px",px); nt.SetBranchAddress("py",py); nt.SetBranchAddress("pz",pz)
        n = nt.GetEntries()
        for i in range(n):
            nt.GetEntry(i)
            if id_v[0]!=5 and id_v[0]!=6: continue
            p = np.sqrt(px[0]**2+py[0]**2+pz[0]**2)
            if p<=0 or ek_v[0]<=0: continue
            th = np.degrees(np.arccos(min(1,max(-1,pz[0]/p))))
            nmu_all += 1
            if tmin <= th < tmax:
                nmu_win += 1
                eks_win.append(ek_v[0])
    f.Close()
    return nshow, nmu_all, nmu_win, np.array(eks_win)

print("=== 75deg: muons per primary, all-theta vs 70-80 window ===")
for p in ["out_75deg/DAT002005.root","out_75deg/DAT002010.root",
          "out_75deg/DAT002015.root","out_75deg/DAT002020.root"]:
    ns, na, nw, ek = muons(p, 70.0, 80.0)
    print(f"{p}: nshow={ns}  all={na}  win={nw}  win/shower={nw/ns:.3f}  "
          f"frac_in_win={nw/na if na else 0:.2f}  <ek>={ek.mean() if len(ek) else 0:.1f}")

print()
print("=== 0deg: for comparison ===")
for p in ["out_0deg/DAT001010.root","out_0deg/DAT001015.root"]:
    ns, na, nw, ek = muons(p, 0.0, 7.0)
    print(f"{p}: nshow={ns}  all={na}  win={nw}  win/shower={nw/ns:.3f}  "
          f"frac_in_win={nw/na if na else 0:.2f}  <ek>={ek.mean() if len(ek) else 0:.1f}")
