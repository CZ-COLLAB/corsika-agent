#!/usr/bin/env python3
"""Analyze QGSJET+urqmd production and emit C-array data in the CRY format."""
import glob, os
import numpy as np
import ROOT

HERE = os.path.dirname(os.path.abspath(__file__))
MUON_MASS = 0.105658

def phi_p(E):
    Em = 1000.0 * E
    return 3.2009e8 * (Em + 920.0)**-4.0 * Em**1.25

EK_MIN, EK_MAX, BINS = 0.3, 3e3, 8
nbins = int(round(np.log10(EK_MAX/EK_MIN) * BINS))
ek_edges = np.logspace(np.log10(EK_MIN), np.log10(EK_MAX), nbins+1)
de = np.diff(ek_edges)

def compute_flux(theta):
    outdir = os.path.join(HERE, f"out_{theta}deg_qgs")
    files = sorted(glob.glob(os.path.join(outdir, "DAT*.root")))
    Ek, Nk, H = [], [], []
    for path in files:
        f = ROOT.TFile.Open(path)
        evt = f.Get("Event"); Eprim = np.zeros(1)
        evt.SetBranchAddress("Eprim", Eprim); evt.GetEntry(0)
        nshow = evt.GetEntries()
        eks = []
        for k in f.GetListOfKeys():
            if k.GetName() != "data_1": continue
            nt = f.Get(f"data_1;{k.GetCycle()}")
            if not nt: continue
            idv = np.zeros(1); ekv = np.zeros(1)
            nt.SetBranchAddress("id", idv); nt.SetBranchAddress("ek", ekv)
            for i in range(nt.GetEntries()):
                nt.GetEntry(i)
                if idv[0] in (5, 6) and ekv[0] > 0:
                    eks.append(ekv[0])
        f.Close()
        h, _ = np.histogram(eks, bins=ek_edges)
        Ek.append(float(Eprim[0])); Nk.append(nshow); H.append(h.astype(float))
    Ek = np.array(Ek); Nk = np.array(Nk); H = np.array(H)
    o = np.argsort(Ek); Ek, Nk, H = Ek[o], Nk[o], H[o]
    lnE = np.log(Ek); dlnE = np.zeros_like(Ek)
    dlnE[0] = (lnE[1]-lnE[0])/2; dlnE[-1] = (lnE[-1]-lnE[-2])/2
    dlnE[1:-1] = (lnE[2:]-lnE[:-2])/2
    w = Ek * phi_p(Ek) * dlnE
    I = (w[:,None] * (H/Nk[:,None])).sum(axis=0) / de
    var = (w[:,None]**2 * H / (Nk[:,None]**2)).sum(axis=0)
    sig = np.sqrt(var) / de
    Ekc = np.sqrt(ek_edges[:-1]*ek_edges[1:])
    return Ekc, I, sig

# user's bin grid
edges = 0.1 * 10.0**(0.15*np.arange(41))
low, high = edges[:-1], edges[1:]
center = (low+high)/2.0
width = high-low

def emit(theta):
    E, I, s = compute_flux(theta)
    p = np.sqrt(E*E + 2*MUON_MASS*E)
    dpdE = p/(E+MUON_MASS)
    dndp, sdndp = I/dpdE, s/dpdE
    flux = np.interp(np.log(center), np.log(p), dndp)
    sig  = np.interp(np.log(center), np.log(p), sdndp)
    valid = (center >= p.min()) & (center <= p.max())
    flux = np.where(valid, flux, 0.0); sig = np.where(valid, sig, 0.0)
    rel = np.where(flux > 0, sig/flux, 0.0)
    print(f"\n// ==================== Agent generated (QGSJET-III+urqmd, {theta}deg) ====================")
    print(f"double corsika_data_qgsiii_urqmd_agent_{theta}deg[{len(center)}][7] = {{")
    for i in range(len(center)):
        print(f"    {{{center[i]:.6e}, {low[i]:.6e}, {high[i]:.6e}, "
              f"{flux[i]:.6e}, {sig[i]:.6e}, {rel[i]:.6e}, {width[i]:.6e}}},")
    print("};")

if __name__ == "__main__":
    emit(0); emit(75)
