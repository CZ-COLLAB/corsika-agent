#!/usr/bin/env python3
"""Integrated muon flux vs zenith angle at Lyon (sea level).

CORSIKA 7.8010, SIBYLL 2.3e (high-energy) + UrQMD (low-energy), CURVED mode.
Only this simulation's own result is shown.
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

W_EXP = -2.7 - (-1.7)   # importance-sampling reweight: E^-1.0


def load_theta(f):
    th = float(re.search(r'events_theta([\d.]+)\.txt', f).group(1))
    e, n = [], []
    for line in open(f):
        a = line.split()
        if len(a) == 2:
            e.append(float(a[0]))
            n.append(float(a[1]))
    e, n = np.array(e), np.array(n)
    w = e ** W_EXP
    prod = w * n
    I = prod.mean()
    err = prod.std(ddof=1) / np.sqrt(len(prod)) if len(prod) > 1 else 0.0
    return th, I, err, len(e), int(n.sum())


def cos2(t, A):
    return A * np.cos(np.radians(t)) ** 2


def cosn(t, A, n):
    return A * np.cos(np.radians(t)) ** n


def main():
    files = sorted(glob.glob(os.path.join(OUT, 'events_theta*.txt')),
                   key=lambda f: float(re.search(r'([\d.]+)', os.path.basename(f)).group(1)))
    rows = [load_theta(f) for f in files]
    rows = [r for r in rows if r[3] > 0]
    th = np.array([r[0] for r in rows])
    I = np.array([r[1] for r in rows])
    err = np.array([r[2] for r in rows])

    print(f"{'theta':>6} {'Nshow':>7} {'Nmu':>9} {'I(rel)':>12} {'err':>11}")
    for r in rows:
        print(f"{r[0]:6.1f} {r[3]:7d} {r[4]:9d} {r[1]:12.4e} {r[2]:11.2e}")

    # fits (on the absolute-scale proxy)
    p2, c2 = curve_fit(cos2, th, I, sigma=err, absolute_sigma=True, p0=[I[0]])
    pn, cn = curve_fit(cosn, th, I, sigma=err, absolute_sigma=True,
                       p0=[I[0], 2.0], maxfev=20000)
    print(f"\nfit I = A cos^2(theta):      A = {p2[0]:.4e} +/- {np.sqrt(c2[0,0]):.2e}")
    print(f"fit I = A cos^n(theta):      A = {pn[0]:.4e}, n = {pn[1]:.3f} "
          f"+/- {np.sqrt(cn[1,1]):.3f}")

    tt = np.linspace(0, 90, 500)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.errorbar(th, I, yerr=err, fmt='o', color='black', ms=6, capsize=3,
                label='CORSIKA 7.8010  SIBYLL 2.3e + UrQMD')
    ax.plot(tt, cosn(tt, *pn), 'k--', lw=1.4,
            label=rf'fit $\cos^{{{pn[1]:.2f}\pm{np.sqrt(cn[1,1]):.2f}}}\theta$')
    ax.plot(tt, cos2(tt, p2[0]), ':', color='0.5', lw=1.2,
            label=r'$\cos^2\theta$')
    ax.set_yscale('log')
    ax.set_xlim(0, 90)
    ax.set_ylim(I.min() * 0.3, I.max() * 3)
    ax.set_xlabel(r'zenith angle $\theta$ [deg]')
    ax.set_ylabel(r'integrated muon flux [arb. units]')
    ax.set_title('Muon flux vs zenith angle - Lyon, sea level\n'
                 'proton, E$^{-2.7}$, 10-10$^6$ GeV')
    ax.grid(False)
    ax.legend(fontsize=9, loc='lower left')
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, 'muon_flux_vs_angle.png'), dpi=150)
    fig.savefig(os.path.join(HERE, 'muon_flux_vs_angle.pdf'))
    print('\nsaved muon_flux_vs_angle.pdf/png')


if __name__ == '__main__':
    main()
