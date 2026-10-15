#!/usr/bin/env python3
"""Full-composition (protons + effective He) muon flux, with full citations.

Primary spectrum: Papini, Grimani & Stephens, Il Nuovo Cimento C 19, N.3 (1996),
Eq. (8) + Table II (solar minimum).  Full composition per the paper's text:
  protons = J_p ; effective He (all Z>1) = J_He + 3.5*J_C+O.
"""
import os, glob, re
import numpy as np
import ROOT

HERE = os.path.dirname(os.path.abspath(__file__))
MUON_MASS = 0.105658
M_NUC = 0.938272

# --- Papini spectra (cm^-2 s^-1 sr^-1 (GeV/nuc)^-1), E = kinetic E per nucleon ---
def J_p(E):
    return 1.8 * (E + 0.92)**-4 * E**1.25
def J_He(E):
    return 0.085 * (E + 0.76)**-3.52 * E**0.77
def J_CO(E):
    return 0.0062 * (E + 1.05)**-3.25 * E**0.5
def J_He_eff(E):
    return J_He(E) + 3.5 * J_CO(E)
def phi_p_tot(Etot):
    return J_p(Etot - M_NUC)          # A=1
def phi_He_tot(Etot):
    return J_He_eff(Etot/4.0 - M_NUC) / 4.0   # A=4

EK_MIN, EK_MAX, BINS = 0.3, 3e3, 8
nbins = int(round(np.log10(EK_MAX/EK_MIN) * BINS))
ek_edges = np.logspace(np.log10(EK_MIN), np.log10(EK_MAX), nbins+1)
de = np.diff(ek_edges)

def compute_component(theta, suffix, phi_tot):
    outdir = os.path.join(HERE, f"out_{theta}deg{suffix}")
    files = sorted(glob.glob(os.path.join(outdir, "DAT*.root")))
    Ek, Nk, H = [], [], []
    for path in files:
        f = ROOT.TFile.Open(path)
        evt = f.Get("Event"); Eprim = np.zeros(1)
        evt.SetBranchAddress("Eprim", Eprim); evt.GetEntry(0)
        nshow = evt.GetEntries(); eks = []
        for k in f.GetListOfKeys():
            if k.GetName() != "data_1": continue
            nt = f.Get(f"data_1;{k.GetCycle()}")
            if not nt: continue
            idv = np.zeros(1); ekv = np.zeros(1)
            nt.SetBranchAddress("id", idv); nt.SetBranchAddress("ek", ekv)
            for i in range(nt.GetEntries()):
                nt.GetEntry(i)
                if idv[0] in (5, 6) and ekv[0] > 0: eks.append(ekv[0])
        f.Close()
        h, _ = np.histogram(eks, bins=ek_edges)
        Ek.append(float(Eprim[0])); Nk.append(nshow); H.append(h.astype(float))
    Ek = np.array(Ek); Nk = np.array(Nk); H = np.array(H)
    o = np.argsort(Ek); Ek, Nk, H = Ek[o], Nk[o], H[o]
    lnE = np.log(Ek); dlnE = np.zeros_like(Ek)
    dlnE[0] = (lnE[1]-lnE[0])/2; dlnE[-1] = (lnE[-1]-lnE[-2])/2
    dlnE[1:-1] = (lnE[2:]-lnE[:-2])/2
    w = Ek * phi_tot(Ek) * dlnE
    I = (w[:,None]*(H/Nk[:,None])).sum(axis=0)/de
    var = (w[:,None]**2 * H/(Nk[:,None]**2)).sum(axis=0)
    sig = np.sqrt(var)/de
    Ekc = np.sqrt(ek_edges[:-1]*ek_edges[1:])
    return Ekc, I, sig

def compute_full(theta):
    Ep, Ip, sp = compute_component(theta, "", phi_p_tot)
    Eh, Ih, sh = compute_component(theta, "_he", phi_He_tot)
    return Ep, Ip + Ih, np.sqrt(sp**2 + sh**2)

if __name__ == "__main__":
    for theta in [0, 75]:
        E, I, s = compute_full(theta)
        np.savetxt(os.path.join(HERE, "results", f"flux_{theta}deg_fullcomp.csv"),
                   np.column_stack([E, I, s]),
                   header="E_kin_GeV  I_cm2_s_sr_GeV  sigma", fmt="%.6e")
        print(f"theta={theta}: full-comp flux saved, "
              f"range [{I[I>0].min():.2e}, {I[I>0].max():.2e}]")
