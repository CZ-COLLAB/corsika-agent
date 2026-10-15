#!/usr/bin/env python3
"""Figure-2-style comparison: CORSIKA muon flux vs empirical models + experimental data.

Empirical formulas (Gaisser, Gaisser/Tang, Bugaev/Reyna, Smith-Duller/Chatzidakis)
and experimental data (L3+C for 0deg, Jokisch 1979 for 75deg) taken from the CRY
analysis macros:
  cryMuonFluxAnalysisWithCorsikanew.C   (0 deg, L3+C data)
  cryMuonFluxAnalysis75_new.C           (75 deg, Jokisch data)
All fluxes are per unit momentum dN/dp [cm^-2 s^-1 sr^-1 (GeV/c)^-1].
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
MUON_MASS = 0.105658

# --------------------------------------------------------------------------
# Empirical formulas (from the CRY macros).  The Gaisser/Tang/SDC families are
# defined per total energy E, so convert to per momentum with dE/dp = p/E.
# --------------------------------------------------------------------------
def fluxGaisser(p, theta_rad):
    A_G, eps_pi, eps_K, BG, gam = 0.14, 115.0/1.1, 810.0/1.1, 0.054, 2.7
    ct = np.cos(theta_rad)
    E = np.sqrt(p*p + MUON_MASS*MUON_MASS)
    fE = A_G * E**-gam * (1.0/(1.0+E*ct/eps_pi) + BG/(1.0+E*ct/eps_K))
    return fE * (p/E)          # dN/dp

def fluxTang(p, theta_rad):
    gam, rc = 2.7, 1e-4
    p1, p2c, p3, p4, p5 = 0.102573, -0.068287, 0.958633, 0.0407253, 0.817285
    ct = np.cos(theta_rad)
    E = np.sqrt(p*p + MUON_MASS*MUON_MASS)
    cos2 = ct*ct + p1*p1 + p2c*ct**p3 + p4*ct**p5
    den = 1.0 + p1*p1 + p2c + p4
    cs = np.sqrt(cos2/den)
    DGT = 2.06e-3*(950.0/cs - 90.0)
    fE = np.zeros_like(E)
    m = E >= 100.0/cs
    fE[m] = 0.14*E[m]**(-gam)*(1.0/(1.0+1.1*E[m]*cs/115.0) + 0.054/(1.0+1.1*E[m]*cs/810.0))
    m = (E < 100.0/cs) & (E >= 1.0/cs)
    Eeff = E[m] + DGT
    pre = 0.14*1.1*(90.0*np.sqrt(ct+0.001)/1030.0)**(4.5/(Eeff*cs))
    fE[m] = pre*E[m]**(-gam)*(1.0/(1.0+1.1*Eeff*cs/115.0) + 0.054/(1.0+1.1*Eeff*cs/810.0) + rc)
    m = E < 1.0/cs
    E2 = 0.3*E[m] + 0.7/cs
    Eeff = E2 + DGT
    pre = 0.14*1.1*(90.0*np.sqrt(ct+0.001)/1030.0)**(4.5/(Eeff*cs))
    fE[m] = pre*E2**(-gam)*(1.0/(1.0+1.1*Eeff*cs/115.0) + 0.054/(1.0+1.1*Eeff*cs/810.0) + rc)
    return fE * (p/E)          # dN/dp

def fluxBugaevReyna(p, theta_rad):
    ct = np.cos(theta_rad)
    pct = p*ct
    y = np.log10(pct)
    exp_val = -(0.0209*y**3 - 0.2555*y**2 + 1.288*y + 0.2455)
    return 2.53e-3 * ct**3 * pct**exp_val

def fluxSDC(p, theta_rad):
    A, r, a, y0 = 2.382e-3, 0.76, 2.5e-3, 1000.0
    Gamma = 8.0/3.0
    b_mu, m_mu, tao_mu0 = 0.8, 105.659e-3, 2.2e-6
    rho_0, c_light, lam_pi = 0.00123, 3e10, 120.0
    b, j_pi = 0.771, 148.16
    ct = np.cos(theta_rad)
    E = np.sqrt(p*p + MUON_MASS*MUON_MASS)
    E_pi = (1.0/r)*(E + a*y0*(1.0/ct - 0.100))
    E_pi = np.where(E_pi > 0, E_pi, np.nan)
    B_mu = b_mu * m_mu * y0 / tao_mu0 / rho_0 / c_light
    exponent = B_mu / (r*E_pi + 100.0*a) / ct
    base = 0.100 * ct * (1.0 - a*(y0/ct - 100.0)/r/E_pi)
    P_mu = np.where(base > 0, base**exponent, np.nan)
    denom = E_pi*ct + b*j_pi
    fE = A * E_pi**-Gamma * P_mu * lam_pi * b * j_pi / denom
    return fE * (p/E)          # dN/dp

# --------------------------------------------------------------------------
# Experimental data (per momentum)
# --------------------------------------------------------------------------
# L3+C (Achard et al. 2004), vertical (0 deg): p (GeV/c), intensity, error
L3C = np.array([
    [23.18, 1.742286e-05, 7.698e-07],
    [30.47, 8.165723e-06, 3.031e-07],
    [38.02, 4.439699e-06, 1.476e-07],
    [45.78, 2.626474e-06, 7.988e-08],
    [54.04, 1.628498e-06, 4.632e-08],
    [63.25, 1.031476e-06, 2.731e-08],
    [74.63, 6.399430e-07, 1.632e-08],
    [90.13, 3.578435e-07, 8.853e-09],
    [114.50, 1.758683e-07, 4.139e-09],
    [161.30, 5.957128e-08, 1.344e-09],
    [243.00, 1.623817e-08, 3.801e-10],
    [381.90, 3.644576e-09, 9.779e-11],
    [687.20, 4.652940e-10, 1.949e-11],
    [1599.00, 2.128011e-11, 2.197e-12]])

# Jokisch et al. 1979 (75 deg): p (GeV/c), intensity, error%
JOKISCH = np.array([
    [1.12, 2.973e-5, 1.45], [1.41, 3.111e-5, 1.07], [1.76, 3.263e-5, 0.85],
    [2.29, 3.168e-5, 0.71], [2.85, 3.068e-5, 0.63], [3.57, 2.848e-5, 0.57],
    [4.49, 2.606e-5, 0.53], [5.66, 2.332e-5, 0.49], [7.12, 2.021e-5, 0.48],
    [8.95, 1.705e-5, 0.46], [11.26, 1.373e-5, 0.46], [14.17, 1.070e-5, 0.47],
    [17.83, 8.029e-6, 0.48], [22.44, 5.708e-6, 0.51], [28.23, 3.964e-6, 0.55],
    [35.52, 2.637e-6, 0.60], [44.70, 1.712e-6, 0.67], [56.25, 1.064e-6, 0.76],
    [70.79, 6.479e-7, 0.86], [89.09, 3.751e-7, 1.01], [112.13, 2.208e-7, 1.18],
    [141.12, 1.234e-7, 1.41], [177.62, 6.632e-8, 1.70], [223.56, 3.735e-8, 2.06],
    [281.39, 1.869e-8, 2.53], [354.18, 9.689e-9, 3.15], [445.81, 5.436e-9, 3.92],
    [625.46, 1.770e-9, 3.87], [990.22, 3.982e-10, 6.30]])

Egrid = np.logspace(np.log10(0.3), np.log10(3e3), 300)

fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.3), sharey=True)
for ax, theta in zip(axes, [0, 75]):
    d = np.loadtxt(f"{HERE}/results/flux_{theta}deg.csv", skiprows=1)
    E, I, s = d[:,0], d[:,1], d[:,2]
    p = np.sqrt(E*E + 2*MUON_MASS*E)
    dEdp = p / (E + MUON_MASS)
    Ip, sp = I*dEdp, s*dEdp
    m = Ip > 0
    ax.errorbar(p[m], Ip[m], yerr=sp[m], fmt='o', ms=4, color=('blue' if theta==0 else 'red'),
                label='CORSIKA (SIBYLL 2.3e + URQMD, p)')
    th = np.radians(theta)
    ax.plot(Egrid, fluxGaisser(Egrid, th), '--', color='#1f77b4', lw=1.2, label='Gaisser')
    ax.plot(Egrid, fluxTang(Egrid, th), '-', color='#ff7f0e', lw=1.4, label='Gaisser/Tang')
    ax.plot(Egrid, fluxBugaevReyna(Egrid, th), '-', color='#9467bd', lw=1.4, label='Bugaev/Reyna')
    ax.plot(Egrid, fluxSDC(Egrid, th), '-', color='#2ca02c', lw=1.2, label='Smith-Duller/Chatzidakis')
    if theta == 0:
        ax.errorbar(L3C[:,0], L3C[:,1], yerr=L3C[:,2], fmt='s', ms=3.5, color='black',
                    label='L3+C (Achard 2004)')
    else:
        ax.errorbar(JOKISCH[:,0], JOKISCH[:,1], yerr=JOKISCH[:,1]*JOKISCH[:,2]/100.0,
                    fmt='s', ms=3.5, color='black', label='Jokisch 1979')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel(r"$\mu$ momentum  $p$ (GeV/c)")
    if theta == 0:
        ax.set_ylabel(r"$dN/(dp\,dA\,d\Omega\,dt)$  (cm$^{-2}$ s$^{-1}$ sr$^{-1}$ (GeV/c)$^{-1}$)")
    ax.set_title(r"$\theta$ = %d$^\circ$" % theta)
    ax.set_xlim(0.3, 3e3)
    ax.set_ylim(1e-13, 3e-2)
    ax.legend(fontsize=6.5, loc='lower left')

plt.tight_layout()
out = f"{HERE}/results/flux_compare_figure2.pdf"
plt.savefig(out, dpi=130)
print("saved", out)
