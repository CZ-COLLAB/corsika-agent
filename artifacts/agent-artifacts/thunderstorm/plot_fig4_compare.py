#!/usr/bin/env python3
"""3x3 comparison figure with digitized original Figure 4 (paper: Thunderstorm 1).

Rows = species (gamma, e±, mu±), columns = field case (0, +2000, -2000 V/cm).
Each panel: blue step line = CORSIKA Agent (50000 showers, no rescaling),
red step line = digitized original. No markers, no grid.

The paper does not state its simulation statistics; the integer assumed here
is N_PAPER = 50000 (magnitude matching gives 41k-58k per curve, with the
well-matching muon curves at 48k-51k), so the reproduction was rerun with
NSHOW=50000 (RUNNR 4008/4009/4010) and needs no scaling.

Output: run/figure4_compare.png/.pdf
"""
import os
import shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

Z_PATH = os.path.expanduser('~/corsika-78010/run/fig4_spectra_50k.npz')
if not os.path.exists(Z_PATH):
    Z_PATH = '/tmp/opencode/fig4_spectra_50k.npz'
Z = np.load(Z_PATH)
DL = os.path.expanduser('~/Downloads')

SPECIES = [
    ('gamma', r'$\gamma$', [('E0', 'E = 0', f'{DL}/gamma_E_0.csv', 'ef0_g'),
                            ('Ep2000', '+2000 V/cm', f'{DL}/gamma_E=2000.csv', 'efp_g'),
                            ('Em2000', '-2000 V/cm', f'{DL}/gamma_E_-2000.csv', 'efm_g')]),
    ('e', r'$e^{\pm}$', [('E0', 'E = 0', f'{DL}/e_E_0.csv', 'ef0_e'),
                         ('Ep2000', '+2000 V/cm', f'{DL}/e_E_2000.csv', 'efp_e'),
                         ('Em2000', '-2000 V/cm', f'{DL}/e_E_-2000.csv', 'efm_e')]),
    ('mu', r'$\mu^{\pm}$', [('E0', 'E = 0', f'{DL}/mu_E_0.csv', 'ef0_m'),
                            ('Ep2000', '+2000 V/cm', f'{DL}/mu_E_2000.csv', 'efp_m'),
                            ('Em2000', '-2000 V/cm', f'{DL}/mu_E_-2000.csv', 'efm_m')]),
]

GRID_LO, GRID_HI, GRID_STEP, MIN_COUNT = -2.1, 3.0, 0.1, 3
OURS_COLOR = 'tab:blue'
PAPER_COLOR = 'tab:red'


def load_digit(f):
    d = np.loadtxt(f, delimiter=',')
    x, y = d[:, 0], d[:, 1]
    o = np.argsort(x)
    return x[o], y[o]


def grid_ednde(ekin):
    """E * dN/dE on a fixed log grid; bins with < MIN_COUNT counts -> NaN."""
    edges = np.arange(GRID_LO, GRID_HI + GRID_STEP / 2, GRID_STEP)
    counts = np.histogram(np.log10(ekin), bins=edges)[0]
    width = 10 ** edges[1:] - 10 ** edges[:-1]
    centers = 0.5 * (edges[:-1] + edges[1:])
    ednde = 10 ** centers * counts / width
    ednde[counts < MIN_COUNT] = np.nan
    return centers, ednde


# ---- load all curves -------------------------------------------------------
curves = {}
for sp, name, cfgs in SPECIES:
    for tag, label, f, key in cfgs:
        x, y = load_digit(f)
        xc, eg = grid_ednde(Z[key])
        curves[(sp, tag)] = dict(x=x, y=y, xc=xc, ednde=eg)

# ---- normalisation: assume the original used N_PAPER showers --------------
# The paper does not state its simulation statistics. From the magnitude
# match the best round integer is N_PAPER = 50000 (per-curve best fit gives
# N = 41k-58k; the well-matching muon curves give 48k-51k).
N_PAPER = 50000
N_OURS = 50000
Cglob = N_PAPER / N_OURS
print(f'N_PAPER = {N_PAPER}, N_OURS = {N_OURS} -> scale = {Cglob:.2f}')
for (sp, tag), c in curves.items():
    m = np.isfinite(c['ednde'])
    e_at_x = 10 ** np.interp(c['x'], c['xc'][m], np.log10(c['ednde'][m]))
    nfit = N_OURS * np.nanmedian(c['y'] / e_at_x)
    print(f'  {sp:>5} {tag:>6}: best-fit N = {nfit:8.0f}')

# ---- global x range --------------------------------------------------------
xs = []
for c in curves.values():
    xs += [c['x'].min(), c['x'].max(), np.nanmin(c['xc']),
           np.nanmax(c['xc'][np.isfinite(c['ednde'])])]
xlim = (max(min(xs) - 0.15, -2.4), min(max(xs) + 0.15, 3.1))

# ---- 3x3 figure ------------------------------------------------------------
fig, axes = plt.subplots(3, 3, figsize=(15.5, 12.5), sharex=True)
for i, (sp, name, cfgs) in enumerate(SPECIES):
    ys = []
    for tag, label, f, key in cfgs:
        c = curves[(sp, tag)]
        both = np.concatenate([c['y'], Cglob * c['ednde']])
        both = both[np.isfinite(both) & (both > 0)]
        ys += [both.min(), both.max()]
    ylim = (min(ys) / 2.5, max(ys) * 2.5)
    for j, (tag, label, f, key) in enumerate(cfgs):
        ax = axes[i, j]
        c = curves[(sp, tag)]
        ax.plot(c['x'], c['y'], drawstyle='steps-mid', color=PAPER_COLOR,
                lw=1.8, label='original (digitized)', zorder=2)
        ax.plot(c['xc'], Cglob * c['ednde'], drawstyle='steps-mid',
                color=OURS_COLOR, lw=2.4,
                label=r'CORSIKA Agent', zorder=3)
        ax.set_yscale('log')
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.grid(False)
        ax.tick_params(labelsize=16)
        if i == 0:
            ax.set_title(label, fontsize=20, pad=8)
        if j == 0:
            ax.set_ylabel(f'{name}   ' + r'$E\,dN/d\ln E$', fontsize=18)
        if i == 2:
            ax.set_xlabel(r'$\log_{10}(E\,/\,\mathrm{GeV})$', fontsize=18)
handles, labels = axes[0, 0].get_legend_handles_labels()
fig.legend(handles, labels, fontsize=22, ncol=2, loc='lower center',
           frameon=False, handlelength=2.5)
fig.tight_layout(rect=[0, 0.065, 1, 1])
RUN_DIR = os.path.expanduser('~/corsika-78010/run')
fig.savefig('/tmp/opencode/figure4_compare.png', dpi=150)
fig.savefig('/tmp/opencode/figure4_compare.pdf')
for src, dst in (('/tmp/opencode/figure4_compare.png', f'{RUN_DIR}/figure4_compare.png'),
                 ('/tmp/opencode/figure4_compare.pdf', f'{RUN_DIR}/figure4_compare.pdf')):
    try:
        shutil.copyfile(src, dst)
        print('saved', dst)
    except OSError as e:
        print(f'WARNING: {dst} is locked ({e}); new version kept at {src}')
