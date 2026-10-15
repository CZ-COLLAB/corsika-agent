#!/usr/bin/env python3
"""Generate CORSIKA steering cards for the He (PRMPAR=402) production.

Full composition: protons + "effective helium" (represents all Z>1 nuclei,
flux = J_He + 3.5*J_C+O from Papini et al. 1996).  He is injected as ^4He
nuclei at total energy per nucleus = 4x the proton total-energy grid (same
energy-per-nucleon coverage).
"""
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CARDS = os.path.join(HERE, "cards")
os.makedirs(CARDS, exist_ok=True)

CORSIKA_BIN = os.path.expanduser('~/corsika-78010/run/corsika78010Linux_SIBYLL_urqmd')
PLOTTER_BIN = os.path.expanduser('~/corsika-78010/run/CorsikaPlottermini')

THETAS = {0: "out_0deg_he", 75: "out_75deg_he"}

# proton total-energy grid: 10 GeV .. 1e5 GeV (5/decade).  He: 4x (per nucleus)
E_PROT_MIN, E_PROT_MAX, PTS = 1e1, 1e5, 5
ndec = int(round(np.log10(E_PROT_MAX / E_PROT_MIN)))
npts = ndec * PTS + 1
prot_energies = np.logspace(np.log10(E_PROT_MIN), np.log10(E_PROT_MAX), npts)
he_energies = 4.0 * prot_energies   # total energy per He nucleus


def nshow_per_point(E_nuc):
    if E_nuc < 1e2:
        return 1000
    if E_nuc < 1e3:
        return 300
    if E_nuc < 1e4:
        return 100
    return 30


def make_card(theta, E, runnr, seed, nshow, outdir, path):
    card = f"""RUNNR   {runnr}
EVTNR   1
SEED    {seed} 0 0
SEED    {seed+1} 0 0
NSHOW   {nshow}
PRMPAR  402
ERANGE  {E:.6g} {E:.6g}
THETAP  {theta}. {theta}.
PHIP    -180. 180.
SIBYLL  T 0
SIBSIG  T
URQMD   T 0
ELMFLG  T T
ECUTS   0.3  0.3  0.003 0.003
OBSLEV  0.
MAGNET  20.40 43.23
PAROUT  T F
DIRECT  {outdir}/
EXIT
"""
    with open(path, "w") as f:
        f.write(card)


jobs = []
runnr = {"0": 5000, "75": 6000}
for theta, outname in THETAS.items():
    outdir = os.path.join(HERE, outname)
    os.makedirs(outdir, exist_ok=True)
    for i, E in enumerate(he_energies):
        E_nuc = E / 4.0
        nshow = nshow_per_point(E_nuc)
        seed = 700000 + theta + i
        r = runnr[str(theta)] + i
        card = os.path.join(CARDS, f"card_he_{theta:02d}deg_E{i:02d}.inp")
        make_card(theta, E, r, seed, nshow, outdir, card)
        jobs.append((theta, E, r, seed, nshow, card, outdir))

jobs_path = os.path.join(HERE, "jobs_he.txt")
with open(jobs_path, "w") as f:
    f.write("# theta  E_gev  runnr  seed  nshow  card  outdir\n")
    for theta, E, r, seed, nshow, card, outdir in jobs:
        f.write(f"{theta}\t{E:.6g}\t{r}\t{seed}\t{nshow}\t{card}\t{outdir}\n")

total0 = sum(j[4] for j in jobs if j[0] == 0)
total75 = sum(j[4] for j in jobs if j[0] == 75)
print(f"Wrote {len(jobs)} He jobs -> {jobs_path}")
print(f"  He total-energy per nucleus: {he_energies[0]:.4g} .. {he_energies[-1]:.4g} GeV")
print(f"  total showers: 0deg={total0}  75deg={total75}")
