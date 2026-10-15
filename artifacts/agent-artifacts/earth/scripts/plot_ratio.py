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

HERE = os.path.dirname(os.path.abspath(__file__))
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
    Ekc = np.sqrt(ek_edges[:-1]*ek_edges[1:])
    p = np.sqrt(Ekc*Ekc + 2*MUON_MASS*Ekc)
    dpdE = p/(Ekc+MUON_MASS)
    return p, I/dpdE   # momentum, dN/dp

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
    px, py = [], []
    for r in rows:
        c = [x.strip() for x in r.split(',')]
        if float(c[3]) > 0: px.append(float(c[0])); py.append(float(c[3]))
    return np.array(px), np.array(py)

C0 = os.path.expanduser('~/cry_v1.7/test/cryMuonFluxAnalysisWithCorsikanew.C')
C75 = os.path.expanduser('~/cry_v1.7/test/cryMuonFluxAnalysis75_new.C')
PREV = {0: {"sibyll": parse_c_array(C0, "corsika_data_urqmd"),
            "qgs": parse_c_array(C0, "corsika_data_qgsiii_urqmd")},
        75: {"sibyll": parse_c_array(C75, "corsika_75_sibyll_v2"),
             "qgs": parse_c_array(C75, "corsika_75_qgsiii_urqmd")}}

L3C = np.array([[23.18,1.742286e-05],[30.47,8.165723e-06],[38.02,4.439699e-06],
    [45.78,2.626474e-06],[54.04,1.628498e-06],[63.25,1.031476e-06],
    [74.63,6.399430e-07],[90.13,3.578435e-07],[114.50,1.758683e-07],
    [161.30,5.957128e-08],[243.00,1.623817e-08],[381.90,3.644576e-09],
    [687.20,4.652940e-10],[1599.00,2.128011e-11]])
JOKISCH = np.array([[1.12,2.973e-5],[1.41,3.111e-5],[1.76,3.263e-5],
    [2.29,3.168e-5],[2.85,3.068e-5],[3.57,2.848e-5],[4.49,2.606e-5],
    [5.66,2.332e-5],[7.12,2.021e-5],[8.95,1.705e-5],[11.26,1.373e-5],
    [14.17,1.070e-5],[17.83,8.029e-6],[22.44,5.708e-6],[28.23,3.964e-6],
    [35.52,2.637e-6],[44.70,1.712e-6],[56.25,1.064e-6],[70.79,6.479e-7],
    [89.09,3.751e-7],[112.13,2.208e-7],[141.12,1.234e-7],[177.62,6.632e-8],
    [223.56,3.735e-8],[281.39,1.869e-8],[354.18,9.689e-9],[445.81,5.436e-9],
    [625.46,1.770e-9],[990.22,3.982e-10]])

def interp_log(xs, ys, xt):
    return np.interp(np.log(xt), np.log(xs), ys)

fig, axes = plt.subplots(1, 2, figsize=(12.5, 5), sharey=True)
for ax, theta in zip(axes, [0, 75]):
    th = np.radians(theta)
    exp = L3C if theta == 0 else JOKISCH
    exp = exp[exp[:,0] >= 10.0]   # match the C code's p>=10 filter
    p_exp, I_exp = exp[:,0], exp[:,1]

    # my data
    for suf, color, lab in [("", 'blue', 'SIBYLL 2.3e + UrQMD (Agent generated)'),
                            ("_qgs", 'red', 'QGSJET-III + UrQMD (Agent generated)')]:
        pm, Im = compute_flux(theta, suf)
        Imod = interp_log(pm, Im, p_exp)
        ax.plot(p_exp, Imod/I_exp, 'o-', ms=4, color=color, label=lab)
    # user's data
    for model, color, ls in [("sibyll", 'blue', '--'), ("qgs", 'red', '--')]:
        d = PREV[theta][model]
        if d is not None:
            Imod = interp_log(d[0], d[1], p_exp)
            ax.plot(p_exp, Imod/I_exp, ls=ls, color=color, lw=1.3,
                    label=('SIBYLL 2.3e + UrQMD' if model=='sibyll' else 'QGSJET-III + UrQMD'))
    # empirical
    ax.plot(p_exp, fluxGaisser(p_exp, th)/I_exp, ':', color='#1f77b4', lw=1.3, label='Gaisser')
    ax.plot(p_exp, fluxTang(p_exp, th)/I_exp, '-', color='#ff7f0e', lw=1.1, label='Gaisser/Tang')
    ax.plot(p_exp, fluxBR(p_exp, th)/I_exp, '-', color='#9467bd', lw=1.1, label='Bugaev/Reyna')

    ax.axhline(1.0, color='gray', lw=1, ls='--')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel(r"$\mu$ momentum  $p$ (GeV/c)")
    if theta == 0:
        ax.set_ylabel(r"Model / Experimental data")
    ax.set_title(r"$\theta$ = %d$^\circ$" % theta)
    ax.set_ylim(0.02, 5.0)
    ax.legend(fontsize=6.3, loc='lower left')

plt.tight_layout()
out = f"{HERE}/results/ratio_0_75deg.pdf"
plt.savefig(out, dpi=130)
print("saved", out)
