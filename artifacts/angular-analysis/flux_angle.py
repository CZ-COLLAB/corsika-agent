#!/usr/bin/env python3
"""Absolute integrated muon flux vs zenith angle at sea level.

Normalisation follows the standard CORSIKA practice (same convention as the
sea-level-muon-flux work):

    I_mu(theta) = sum_k [ Phi_p(E_k) * dE_k ] * [ N_mu(E_k, theta) / N_k ]
                = int dE_p  Phi_p(E_p) * <N_mu(E_p, theta)>

    Phi_p = Papini/Grimani/Stephens primary proton spectrum (solar minimum)
            J(E) = 3.2009e9 (E[MeV]+920)^-4 E[MeV]^1.25   [/(MeV s m^2 sr)]
            -> 3.2009e8 (Em+920)^-4 Em^1.25  [cm^-2 s^-1 sr^-1 GeV^-1]
    N_mu  = TOTAL muons at sea level (all directions) per primary
    N_k   = number of showers

Units: cm^-2 s^-1 sr^-1.

The showers were importance-sampled from E^-1.7 on [10, 10^6] GeV, so each
event carries the weight Phi_p(E)/p_samp(E) with p_samp(E) = E^-1.7 / Z,
    Z = int_10^1e6 E^-1.7 dE = 0.284947.
"""
import os
import glob
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
RES = os.path.join(HERE, 'results')

# sampling distribution normalisation (ESLOPE -1.7, ERANGE 1e1..1e6)
Z_SAMP = (10 ** -0.7 - (1e6) ** -0.7) / 0.7


def phi_p(E):
    """Papini/Grimani/Stephens proton spectrum, cm^-2 s^-1 sr^-1 GeV^-1."""
    Em = 1000.0 * E
    return 3.2009e8 * (Em + 920.0) ** -4.0 * Em ** 1.25


def load_theta(f):
    th = float(re.search(r'events_theta([\d.]+)\.txt', f).group(1))
    e, n = [], []
    for line in open(f):
        a = line.split()
        if len(a) == 2:
            e.append(float(a[0]))
            n.append(float(a[1]))
    e, n = np.array(e), np.array(n)
    g = phi_p(e) * e ** 1.7 * n          # Phi_p/p_samp * N_mu
    I = Z_SAMP * g.mean()                # cm^-2 s^-1 sr^-1
    err = Z_SAMP * g.std(ddof=1) / np.sqrt(len(g)) if len(g) > 1 else 0.0
    return th, I, err, len(e), int(n.sum())


def cos2(t, A):
    return A * np.cos(np.radians(t)) ** 2


# --- analytic sea-level muon-flux models with angular dependence ---------
# Ported verbatim from the CRY analysis macro
# cry_v1.7/test/cryMuonFluxAnalysisWithCorsikanew.C
# (also matches Su et al., Front. Energy Res. 9 (2021) 750159).
MM = 0.105658
GAMMA = 2.7


def _costar(ct):
    p1, p2, p3, p4, p5 = 0.102573, -0.068287, 0.958633, 0.0407253, 0.817285
    return np.sqrt((ct * ct + p1 * p1 + p2 * ct ** p3 + p4 * ct ** p5)
                   / (1.0 + p1 * p1 + p2 + p4))


def gaisser_p(p, theta):
    """Gaisser model, dN/dp [cm^-2 s^-1 sr^-1 (GeV/c)^-1]."""
    ct = np.cos(np.radians(theta))
    E = np.sqrt(p * p + MM * MM)
    return (0.14 * E ** -GAMMA
            * (1.0 / (1.0 + E * ct / (115.0 / 1.1))
               + 0.054 / (1.0 + E * ct / (810.0 / 1.1))) * (p / E))


def gaisser_tang_p(p, theta):
    """Gaisser/Tang segmented model, dN/dp."""
    p = np.asarray(p, float)
    ct = np.cos(np.radians(theta))
    cts = _costar(ct)
    E = np.sqrt(p * p + MM * MM)
    D = 2.06e-3 * (950.0 / cts - 90.0)
    base = 90.0 * np.sqrt(ct + 0.001) / 1030.0
    f = np.empty_like(E)
    b1 = E >= 100.0 / cts
    b2 = (E >= 1.0 / cts) & (~b1)
    b3 = ~(b1 | b2)
    f[b1] = 0.14 * E[b1] ** -GAMMA * (1.0 / (1.0 + 1.1 * E[b1] * cts / 115.0)
                                      + 0.054 / (1.0 + 1.1 * E[b1] * cts / 810.0))
    Et = E + D
    pre = 0.14 * 1.1 * base ** (4.5 / (Et * cts))
    f[b2] = pre[b2] * E[b2] ** -GAMMA * (
        1.0 / (1.0 + 1.1 * Et[b2] * cts / 115.0)
        + 0.054 / (1.0 + 1.1 * Et[b2] * cts / 810.0) + 1e-4)
    Ee = 0.3 * E + 0.7 / cts
    pre3 = 0.14 * 1.1 * base ** (4.5 / ((Ee + D) * cts))
    f[b3] = pre3[b3] * Ee[b3] ** -GAMMA * (
        1.0 / (1.0 + 1.1 * (Ee[b3] + D) * cts / 115.0)
        + 0.054 / (1.0 + 1.1 * (Ee[b3] + D) * cts / 810.0) + 1e-4)
    return f * (p / E)


def bugaev_reyna_p(p, theta):
    """Bugaev/Reyna model, dN/dp."""
    ct = np.cos(np.radians(theta))
    y = np.log10(p * ct)
    return 2.53e-3 * ct ** 3 * (p * ct) ** -(
        0.0209 * y ** 3 - 0.2555 * y ** 2 + 1.288 * y + 0.2455)


def sdc_p(p, theta):
    """Smith & Duller / Chatzidakis model, dN/dp."""
    p = np.asarray(p, float)
    ct = np.cos(np.radians(theta))
    E = np.sqrt(p * p + MM * MM)
    A, r, a, y0 = 2.382e-3, 0.76, 2.5e-3, 1000.0
    G, b_mu, m_mu, tau0 = 8.0 / 3.0, 0.8, 105.659e-3, 2.2e-6
    rho0, c, lam, b, jpi = 0.00123, 3e10, 120.0, 0.771, 148.16
    B_mu = b_mu * m_mu * y0 / tau0 / rho0 / c / 100.0
    Epi = (1.0 / r) * (E + a * y0 * (1.0 / ct - 0.1))
    baseP = 0.1 * ct * (1.0 - a * (y0 / ct - 100.0) / r / Epi)
    ok = (Epi > 0) & (baseP > 0)
    out = np.zeros_like(E)
    P_mu = baseP[ok] ** (B_mu / (r * Epi[ok] + 100.0 * a) / ct)
    out[ok] = (A * Epi[ok] ** -G * P_mu * lam * b * jpi
               / (Epi[ok] * ct + b * jpi) * (p[ok] / E[ok]))
    return out


def model_flux(model, theta, pmin=1.0, pmax=1e5, npts=6000):
    """Integrated flux vs theta [cm^-2 s^-1 sr^-1]."""
    p = np.logspace(np.log10(pmin), np.log10(pmax), npts)
    return np.trapz(model(p, theta) * p, np.log(p))


def main():
    os.makedirs(RES, exist_ok=True)
    files = sorted(glob.glob(os.path.join(OUT, 'events_theta*.txt')),
                   key=lambda f: float(re.search(r'([\d.]+)', os.path.basename(f)).group(1)))
    rows = [load_theta(f) for f in files]
    rows = [r for r in rows if r[3] > 0]
    th = np.array([r[0] for r in rows])
    I = np.array([r[1] for r in rows])
    err = np.array([r[2] for r in rows])

    print(f"{'theta':>6} {'Nshow':>7} {'Nmu':>9} {'I(cm^-2 s^-1 sr^-1)':>20} {'err':>11}")
    for r in rows:
        print(f"{r[0]:6.1f} {r[3]:7d} {r[4]:9d} {r[1]:20.4e} {r[2]:11.2e}")

    p2, c2 = curve_fit(cos2, th, I, sigma=err, absolute_sigma=True, p0=[I[0]])
    A, dA = p2[0], np.sqrt(c2[0, 0])
    chi2 = np.sum(((I - cos2(th, A)) / err) ** 2)
    dof = len(th) - 1
    print(f"\nfit I = A cos^2(theta):  A = {A:.4e} +/- {dA:.2e} cm^-2 s^-1 sr^-1"
          f"   (chi2/dof = {chi2:.1f}/{dof} = {chi2/dof:.2f})")

    np.savetxt(os.path.join(RES, 'flux_vs_angle.csv'),
               np.column_stack([th, I, err]),
               header='theta_deg  I_cm-2_s-1_sr-1  sigma', fmt='%.6e')

    tt = np.linspace(0, 90, 500)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.errorbar(th, I, yerr=err, fmt='o', color='black', ms=6, capsize=3,
                label='CORSIKA 7.8010  SIBYLL 2.3e + UrQMD')
    ax.plot(tt, cos2(tt, A), 'k--', lw=1.4,
            label=rf'fit $A\cos^2\theta$,  $A={A:.2e}$')
    gt = np.array([model_flux(gaisser_tang_p, t) for t in tt])
    ry = np.array([model_flux(bugaev_reyna_p, t) for t in tt])
    ax.plot(tt, ry, '-', color='tab:green', lw=1.8, label='Bugaev/Reyna')
    ax.plot(tt, gt, '-', color='magenta', lw=1.6, label='Gaisser/Tang')
    print(f"\nGaisser/Tang I(0) = {model_flux(gaisser_tang_p, 0.0):.3e} cm^-2 s^-1 sr^-1")
    print(f"Bugaev/Reyna I(0) = {model_flux(bugaev_reyna_p, 0.0):.3e} cm^-2 s^-1 sr^-1")
    ax.set_yscale('log')
    ax.set_xlim(0, 90)
    ax.set_ylim(I.min() * 0.3, I.max() * 3)
    ax.set_xlabel(r'zenith angle $\theta$ [deg]')
    ax.set_ylabel(r'integrated $\mu$ flux  [cm$^{-2}$ s$^{-1}$ sr$^{-1}$]')
    ax.grid(False)
    ax.legend(fontsize=9, loc='lower left')
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, 'muon_flux_vs_angle.png'), dpi=150)
    fig.savefig(os.path.join(HERE, 'muon_flux_vs_angle.pdf'))
    print('\nsaved muon_flux_vs_angle.pdf/png and results/flux_vs_angle.csv')


if __name__ == '__main__':
    main()
