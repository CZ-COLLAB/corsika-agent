#!/usr/bin/env python3
"""Isotropic-injection muon flux: select muons in angular bins, divide by bin
solid angle, weight by Papini primary spectrum.

I_mu(E_mu, theta) = sum_k [ Phi_p(E_k) dE_k ] * [ N_mu,bin,k / (N_k * dOmega_bin) ]
                    / dE_mu
"""
import os, glob
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

BINS_ANGLE = {"vertical": (0.0, 5.0), "75deg": (70.0, 80.0)}

def dOmega(t1, t2):
    return 2*np.pi*(np.cos(np.radians(t1)) - np.cos(np.radians(t2)))

def compute_flux(theta_bin):
    t1, t2 = BINS_ANGLE[theta_bin]
    dOm = dOmega(t1, t2)
    outdir = os.path.join(HERE, "out_iso")
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
            px = np.zeros(1); py = np.zeros(1); pz = np.zeros(1)
            nt.SetBranchAddress("id", idv); nt.SetBranchAddress("ek", ekv)
            nt.SetBranchAddress("px", px); nt.SetBranchAddress("py", py); nt.SetBranchAddress("pz", pz)
            for i in range(nt.GetEntries()):
                nt.GetEntry(i)
                if idv[0] not in (5, 6): continue
                p = np.sqrt(px[0]**2 + py[0]**2 + pz[0]**2)
                if p <= 0 or ekv[0] <= 0: continue
                th = np.degrees(np.arccos(min(1.0, max(-1.0, pz[0]/p))))
                if t1 <= th < t2:
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
    I = (w[:,None] * (H/(Nk[:,None]*dOm))).sum(axis=0) / de
    var = (w[:,None]**2 * H/(Nk[:,None]*dOm)**2).sum(axis=0)
    sig = np.sqrt(var) / de
    Ekc = np.sqrt(ek_edges[:-1]*ek_edges[1:])
    return Ekc, I, sig

if __name__ == "__main__":
    for tb in ["vertical", "75deg"]:
        E, I, s = compute_flux(tb)
        tag = "0deg" if tb == "vertical" else "75deg"
        np.savetxt(os.path.join(HERE, "results", f"flux_{tag}_iso.csv"),
                   np.column_stack([E, I, s]),
                   header="E_kin_GeV  I_cm2_s_sr_GeV  sigma", fmt="%.6e")
        m = I > 0
        print(f"{tb}: {np.sum(m)} non-empty bins, "
              f"flux@100GeV = {I[np.argmin(np.abs(E-100))]:.3e}")
