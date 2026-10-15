#!/usr/bin/env python3
"""Full-composition (p + effective He) figures: flux comparison + ratio.

Primary: Papini, Grimani & Stephens, Nuovo Cimento C 19, N.3 (1996).
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
MUON_MASS = 0.105658

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
def fluxSDC(p, th):
    A,r,a,y0 = 2.382e-3,0.76,2.5e-3,1000.0; G = 8.0/3.0
    bm,mm,tm = 0.8,105.659e-3,2.2e-6; rho,c,lam = 0.00123,3e10,120.0; b,jp = 0.771,148.16
    ct = np.cos(th); E = np.sqrt(p*p+MUON_MASS*MUON_MASS)
    Ep = (1/r)*(E + a*y0*(1/ct-0.100)); Ep = np.where(Ep>0, Ep, np.nan)
    B = bm*mm*y0/tm/rho/c
    base = 0.100*ct*(1-a*(y0/ct-100)/r/Ep)
    Pm = np.where(base>0, base**(B/(r*Ep+100*a)/ct), np.nan)
    den = Ep*ct+b*jp
    fE = A*Ep**-G*Pm*lam*b*jp/den
    return fE*(p/E)

L3C = np.array([[23.18,1.742286e-05],[30.47,8.165723e-06],[38.02,4.439699e-06],
    [45.78,2.626474e-06],[54.04,1.628498e-06],[63.25,1.031476e-06],
    [74.63,6.399430e-07],[90.13,3.578435e-07],[114.50,1.758683e-07],
    [161.30,5.957128e-08],[243.00,1.623817e-08],[381.90,3.644576e-09],
    [687.20,4.652940e-10],[1599.00,2.128011e-11]])
JOKISCH = np.array([[1.12,2.973e-5],[1.41,3.111e-5],[1.76,3.263e-5],[2.29,3.168e-5],
    [2.85,3.068e-5],[3.57,2.848e-5],[4.49,2.606e-5],[5.66,2.332e-5],
    [7.12,2.021e-5],[8.95,1.705e-5],[11.26,1.373e-5],[14.17,1.070e-5],
    [17.83,8.029e-6],[22.44,5.708e-6],[28.23,3.964e-6],[35.52,2.637e-6],
    [44.70,1.712e-6],[56.25,1.064e-6],[70.79,6.479e-7],[89.09,3.751e-7],
    [112.13,2.208e-7],[141.12,1.234e-7],[177.62,6.632e-8],[223.56,3.735e-8],
    [281.39,1.869e-8],[354.18,9.689e-9],[445.81,5.436e-9],[625.46,1.770e-9],
    [990.22,3.982e-10]])

Egrid = np.logspace(np.log10(0.3), np.log10(3e3), 300)

def load(theta, fullcomp=True):
    name = f"flux_{theta}deg_fullcomp.csv" if fullcomp else f"flux_{theta}deg.csv"
    d = np.loadtxt(f"{HERE}/results/{name}", skiprows=1)
    E, I, s = d[:,0], d[:,1], d[:,2]
    p = np.sqrt(E*E + 2*MUON_MASS*E)
    dpdE = p/(E+MUON_MASS)
    return p, I/dpdE, s/dpdE

# ---- figure 1: flux comparison ----
fig, axes = plt.subplots(1, 2, figsize=(13, 5.4), sharey=True)
for ax, theta in zip(axes, [0, 75]):
    th = np.radians(theta)
    # protons only (lighter)
    pp, Ipp, spp = load(theta, fullcomp=False)
    mp = Ipp > 0
    ax.errorbar(pp[mp], Ipp[mp], yerr=spp[mp], fmt='o', ms=3, color='steelblue',
                alpha=0.7, label='CORSIKA protons only')
    # full composition
    p, Ip, sp = load(theta, fullcomp=True)
    m = Ip > 0
    ax.errorbar(p[m], Ip[m], yerr=sp[m], fmt='o', ms=4, color='darkred',
                label='CORSIKA full comp. (p + He, Papini)')
    ax.plot(Egrid, fluxGaisser(Egrid, th), '--', color='#1f77b4', lw=1.2, label='Gaisser')
    ax.plot(Egrid, fluxTang(Egrid, th), '-', color='#ff7f0e', lw=1.4, label='Gaisser/Tang')
    ax.plot(Egrid, fluxBR(Egrid, th), '-', color='#9467bd', lw=1.4, label='Bugaev/Reyna')
    ax.plot(Egrid, fluxSDC(Egrid, th), '-', color='#2ca02c', lw=1.2, label='Smith-Duller/Chatzidakis')
    if theta == 0:
        ax.errorbar(L3C[:,0], L3C[:,1], yerr=L3C[:,1]*0.05, fmt='s', ms=3.5, color='black', label='L3+C (Achard 2004)')
    else:
        ax.errorbar(JOKISCH[:,0], JOKISCH[:,1], yerr=JOKISCH[:,1]*0.05, fmt='s', ms=3.5, color='black', label='Jokisch 1979')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel(r"$\mu$ momentum  $p$ (GeV/c)")
    if theta == 0:
        ax.set_ylabel(r"$dN/(dp\,dA\,d\Omega\,dt)$  (cm$^{-2}$ s$^{-1}$ sr$^{-1}$ (GeV/c)$^{-1}$)")
    ax.set_title(r"$\theta$ = %d$^\circ$" % theta)
    ax.set_xlim(0.3, 3e3); ax.set_ylim(1e-12, 3e-2)
    ax.legend(fontsize=6.3, loc='lower left')
plt.tight_layout()
out1 = f"{HERE}/results/flux_fullcomp_comparison.pdf"
plt.savefig(out1, dpi=130)
print("saved", out1)

# ---- figure 2: ratio ----
fig, axes = plt.subplots(1, 2, figsize=(12.5, 5), sharey=True)
for ax, theta in zip(axes, [0, 75]):
    th = np.radians(theta)
    exp = (L3C if theta == 0 else JOKISCH); exp = exp[exp[:,0] >= 10.0]
    p_exp, I_exp = exp[:,0], exp[:,1]
    # protons only
    pm0, Im0, _ = load(theta, fullcomp=False)
    Imod0 = np.interp(np.log(p_exp), np.log(pm0), Im0)
    ax.plot(p_exp, Imod0/I_exp, 'o-', ms=3, color='steelblue', alpha=0.7, label='CORSIKA protons only')
    # full composition
    pm, Im, _ = load(theta, fullcomp=True)
    Imod = np.interp(np.log(p_exp), np.log(pm), Im)
    ax.plot(p_exp, Imod/I_exp, 'o-', ms=4, color='darkred', label='CORSIKA full comp.')
    ax.plot(p_exp, fluxGaisser(p_exp, th)/I_exp, ':', color='#1f77b4', lw=1.3, label='Gaisser')
    ax.plot(p_exp, fluxTang(p_exp, th)/I_exp, '-', color='#ff7f0e', lw=1.1, label='Gaisser/Tang')
    ax.plot(p_exp, fluxBR(p_exp, th)/I_exp, '-', color='#9467bd', lw=1.1, label='Bugaev/Reyna')
    ax.axhline(1.0, color='gray', lw=1, ls='--')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel(r"$\mu$ momentum  $p$ (GeV/c)")
    if theta == 0: ax.set_ylabel(r"Model / Experimental data")
    ax.set_title(r"$\theta$ = %d$^\circ$" % theta)
    ax.set_ylim(0.1, 5.0)
    ax.legend(fontsize=6.5, loc='lower left')
plt.tight_layout()
out2 = f"{HERE}/results/ratio_fullcomp.pdf"
plt.savefig(out2, dpi=130)
print("saved", out2)
