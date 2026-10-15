import ROOT, numpy as np, glob, os

def diag(path):
    f = ROOT.TFile.Open(path)
    evt = f.Get("Event")
    nshow = evt.GetEntries()
    Eprim = np.zeros(1); Theta = np.zeros(1); Nmu = np.zeros(1)
    evt.SetBranchAddress("Eprim", Eprim)
    evt.SetBranchAddress("Theta", Theta)
    evt.SetBranchAddress("Nmu", Nmu)
    evt.GetEntry(0)
    nt = f.Get("data_1;1")
    n_nt = nt.GetEntries() if nt else 0
    f.Close()
    return float(Eprim[0]), float(Theta[0]), int(Nmu[0]), nshow, n_nt

for d in ["out_0deg", "out_75deg"]:
    files = sorted(glob.glob(os.path.join(d, "DAT*.root")))
    print(f"=== {d} ({len(files)} files) ===")
    for p in files[::4]:  # sample
        E, th, nmu0, nshow, n_nt = diag(p)
        print(f"  {os.path.basename(p)}: E={E:.3g} theta={th:.2f} Nmu(evt0)={nmu0} nshow={nshow} ntuple_entries={n_nt}")
