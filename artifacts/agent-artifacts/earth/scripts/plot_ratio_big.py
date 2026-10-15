#!/usr/bin/env python3
"""Ratio plots: Model / Experimental Data vs muon momentum.

Same logic as plotMuonRatio0 / plotMuonRatio75 in the CRY macros: at each
experimental data point (p, I_exp), evaluate each model flux I_model(p) and plot
I_model / I_exp.  ratio = 1 means perfect agreement.

Models: my agent SIBYLL/QGS (solid), user's existing SIBYLL/QGS (dashed),
Gaisser/Tang, Bugaev/Reyna (empirical).
"""
import os, glob, re
import numpy as np
import ROOT
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({'font.size': 16, 'axes.labelsize': 17,
                     'xtick.labelsize': 15, 'ytick.labelsize': 15,
                     'legend.fontsize': 10, 'axes.titlesize': 18})

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.path.normpath(os.path.join(HERE, "..", "..", "paper"))
MUON_MASS = 0.105658

def phi_p(E):
    Em = 1000.0 * E
    return 3.2009e8 * (Em + 920.0)**-4.0 * Em**1.25

EK_MIN, EK_MAX, BINS = 0.3, 3e3, 8
nbins = int(round(np.log10(EK_MAX/EK_MIN) * BINS))
ek_edges = np.logspace(np.log10(EK_MIN), np.log10(EK_MAX), nbins+1)
de = np.diff(ek_edges)

def compute_flux(theta, suffix):
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
    w = Ek * phi_p(Ek) * dlnE
    I = (w[:,None]*(H/Nk[:,None])).sum(axis=0)/de
    var = (w[:,None]**2 * H / (Nk[:,None]**2)).sum(axis=0)
    sig = np.sqrt(var)/de
    Ekc = np.sqrt(ek_edges[:-1]*ek_edges[1:])
    p = np.sqrt(Ekc*Ekc + 2*MUON_MASS*Ekc)
    dpdE = p/(Ekc+MUON_MASS)
    return p, I/dpdE, sig/dpdE   # momentum, dN/dp, sigma

def fluxGaisser(p, th):
    A, epi, ek, BG, g = 0.14, 115/1.1, 810/1.1, 0.054, 2.7
    ct = np.cos(th); E = np.sqrt(p*p + MUON_MASS*MUON_MASS)
    return A*E**-g*(1/(1+E*ct/epi)+BG/(1+E*ct/ek))*(p/E)

def fluxTang(p, th):
    g, rc = 2.7, 1e-4
    p1,p2,p3,p4,p5 = 0.102573,-0.068287,0.958633,0.0407253,0.817285
    ct = np.cos(th); E = np.sqrt(p*p + MUON_MASS*MUON_MASS)
    cs = np.sqrt((ct*ct+p1*p1+p2*ct**p3+p4*ct**p5)/(1+p1*p1+p2+p4))
    DGT = 2.06e-3*(950.0/cs-90.0)
    fE = np.zeros_like(E)
    m = E >= 100.0/cs
    fE[m] = 0.14*E[m]**-g*(1/(1+1.1*E[m]*cs/115)+0.054/(1+1.1*E[m]*cs/810))
    m = (E < 100/cs) & (E >= 1/cs)
    Ee = E[m]+DGT; pre = 0.14*1.1*(90*np.sqrt(ct+0.001)/1030)**(4.5/(Ee*cs))
    fE[m] = pre*E[m]**-g*(1/(1+1.1*Ee*cs/115)+0.054/(1+1.1*Ee*cs/810)+rc)
    m = E < 1/cs
    E2 = 0.3*E[m]+0.7/cs; Ee = E2+DGT; pre = 0.14*1.1*(90*np.sqrt(ct+0.001)/1030)**(4.5/(Ee*cs))
    fE[m] = pre*E2**-g*(1/(1+1.1*Ee*cs/115)+0.054/(1+1.1*Ee*cs/810)+rc)
    return fE*(p/E)

def fluxBR(p, th):
    ct = np.cos(th); pct = p*ct; y = np.log10(pct)
    ex = -(0.0209*y**3-0.2555*y**2+1.288*y+0.2455)
    return 2.53e-3*ct**3*pct**ex

def parse_c_array(fname, arr):
    txt = open(fname).read()
    m = re.search(r'(?m)^\s*double\s+' + re.escape(arr) + r'\b.*?=\s*\{(.*?)\};', txt, re.S)
    if not m: return None
    rows = re.findall(r'\{([^}]*)\}', m.group(1))
    px, py, pe = [], [], []
    for r in rows:
        c = [x.strip() for x in r.split(',')]
        Ec, fE, eE = float(c[0]), float(c[3]), float(c[4])
        if fE <= 0 or eE >= 0.5*fE or Ec <= MUON_MASS:
            continue
        p = np.sqrt(Ec*Ec - MUON_MASS*MUON_MASS)
        px.append(p); py.append(fE*p/Ec); pe.append(eE*p/Ec)
    return np.array(px), np.array(py), np.array(pe)

C0 = os.path.expanduser('~/cry_v1.7/test/cryMuonFluxAnalysisWithCorsikanew.C')
C75 = os.path.expanduser('~/cry_v1.7/test/cryMuonFluxAnalysis75_new.C')
PREV = {0: {"sibyll": parse_c_array(C0, "corsika_data_urqmd"),
            "qgs": parse_c_array(C0, "corsika_data_qgsiii_urqmd")},
        75: {"sibyll": parse_c_array(C75, "corsika_75_sibyll_v2"),
             "qgs": parse_c_array(C75, "corsika_75_qgsiii_urqmd")}}

L3C = np.array([
    [23.18,1.742286e-05,7.698e-07],[30.47,8.165723e-06,3.031e-07],
    [38.02,4.439699e-06,1.476e-07],[45.78,2.626474e-06,7.988e-08],
    [54.04,1.628498e-06,4.632e-08],[63.25,1.031476e-06,2.731e-08],
    [74.63,6.399430e-07,1.632e-08],[90.13,3.578435e-07,8.853e-09],
    [114.50,1.758683e-07,4.139e-09],[161.30,5.957128e-08,1.344e-09],
    [243.00,1.623817e-08,3.801e-10],[381.90,3.644576e-09,9.779e-11],
    [687.20,4.652940e-10,1.949e-11],[1599.00,2.128011e-11,2.197e-12]])
JOKISCH = np.array([
    [1.12,2.973e-5,1.45],[1.41,3.111e-5,1.07],[1.76,3.263e-5,0.85],
    [2.29,3.168e-5,0.71],[2.85,3.068e-5,0.63],[3.57,2.848e-5,0.57],
    [4.49,2.606e-5,0.53],[5.66,2.332e-5,0.49],[7.12,2.021e-5,0.48],
    [8.95,1.705e-5,0.46],[11.26,1.373e-5,0.46],[14.17,1.070e-5,0.47],
    [17.83,8.029e-6,0.48],[22.44,5.708e-6,0.51],[28.23,3.964e-6,0.55],
    [35.52,2.637e-6,0.60],[44.70,1.712e-6,0.67],[56.25,1.064e-6,0.76],
    [70.79,6.479e-7,0.86],[89.09,3.751e-7,1.01],[112.13,2.208e-7,1.18],
    [141.12,1.234e-7,1.41],[177.62,6.632e-8,1.70],[223.56,3.735e-8,2.06],
    [281.39,1.869e-8,2.53],[354.18,9.689e-9,3.15],[445.81,5.436e-9,3.92],
    [625.46,1.770e-9,3.87],[990.22,3.982e-10,6.30]])

def interp_log(xs, ys, xt):
    return np.interp(np.log(xt), np.log(xs), ys)

fig, axes = plt.subplots(1, 2, figsize=(12.5, 5), sharey=True)
for ax, theta in zip(axes, [0, 75]):
    th = np.radians(theta)
    exp = L3C if theta == 0 else JOKISCH
    exp = exp[exp[:,0] >= 10.0]   # match the C code's p>=10 filter
    p_exp, I_exp = exp[:,0], exp[:,1]
    sig_exp = exp[:,2] if theta == 0 else exp[:,1]*exp[:,2]/100.0

    # my data
    for suf, color, lab in [("", 'blue', 'SIBYLL 2.3e + UrQMD (Agent generated)'),
                            ("_qgs", 'red', 'QGSJET-III + UrQMD (Agent generated)')]:
        pm, Im, sm = compute_flux(theta, suf)
        Imod = interp_log(pm, Im, p_exp)
        smod = interp_log(pm, sm, p_exp)
        ratio = Imod/I_exp
        rerr = ratio*np.sqrt((smod/np.maximum(Imod, 1e-300))**2 + (sig_exp/I_exp)**2)
        ax.errorbar(p_exp, ratio, yerr=rerr, fmt='o-', ms=6, lw=1.5,
                    capsize=2, elinewidth=1.2, color=color, label=lab)
    # user's data
    for model, color, ls in [("sibyll", 'blue', '--'), ("qgs", 'red', '--')]:
        d = PREV[theta][model]
        if d is not None:
            Imod = interp_log(d[0], d[1], p_exp)
            smod = interp_log(d[0], d[2], p_exp)
            ratio = Imod/I_exp
            rerr = ratio*np.sqrt((smod/np.maximum(Imod, 1e-300))**2 + (sig_exp/I_exp)**2)
            ax.errorbar(p_exp, ratio, yerr=rerr, fmt='o', ms=4, lw=1.9, ls=ls,
                        capsize=2, elinewidth=1.0, color=color,
                        label=('SIBYLL 2.3e + UrQMD' if model=='sibyll' else 'QGSJET-III + UrQMD'))
    # empirical
    ax.plot(p_exp, fluxGaisser(p_exp, th)/I_exp, ':', color='#1f77b4', lw=1.8, label='Gaisser')
    ax.plot(p_exp, fluxTang(p_exp, th)/I_exp, '-', color='#ff7f0e', lw=1.7, label='Gaisser/Tang')
    ax.plot(p_exp, fluxBR(p_exp, th)/I_exp, '-', color='#9467bd', lw=1.7, label='Bugaev/Reyna')

    ax.axhline(1.0, color='gray', lw=1.3, ls='--')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel(r"$\mu$ momentum  $p$ (GeV/c)")
    if theta == 0:
        ax.set_ylabel(r"Model / Experimental data")
    ax.set_title(r"$\theta$ = %d$^\circ$" % theta)
    ax.set_ylim(0.02, 5.0)
    ax.legend(fontsize=10, loc='lower left', framealpha=0.9)

plt.tight_layout()
out = f"{PAPER}/ratio_0_75deg.pdf"
tmp = out + ".tmp.pdf"
plt.savefig(tmp, dpi=130)
try:
    os.replace(tmp, out)
    print("saved", out)
except PermissionError:
    fallback = f"{PAPER}/ratio_0_75deg_new.pdf"
    os.replace(tmp, fallback)
    print("LOCKED -> saved", fallback)
