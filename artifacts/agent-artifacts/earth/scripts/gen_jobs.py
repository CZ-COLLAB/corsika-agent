#!/usr/bin/env python3
"""
Generate CORSIKA steering cards for the sea-level muon flux production.

Run1: protons only, fixed zenith (0 deg and 75 deg), log-spaced primary energy
grid 10 GeV - 1e5 GeV, 5 points/decade. Shower count per point decreases with
energy (cheap low-energy showers dominate the flux weight).

Output:
  cards/  - one steering card per (theta, energy) job
  jobs.txt - TSV job list: theta  energy_gev  runnr  seed  nshow  card  outdir
"""
import os
import sys
import numpy as np

MODEL = sys.argv[1] if len(sys.argv) > 1 else "sibyll"
assert MODEL in ("sibyll", "qgs"), "model must be 'sibyll' or 'qgs'"

HERE = os.path.dirname(os.path.abspath(__file__))
CARDS = os.path.join(HERE, "cards")
os.makedirs(CARDS, exist_ok=True)

CORSIKA_BIN = (os.path.expanduser('~/corsika-78010/run/corsika78010Linux_QGSIII_urqmd')
               if MODEL == "qgs" else
               os.path.expanduser('~/corsika-78010/run/corsika78010Linux_SIBYLL_urqmd'))
PLOTTER_BIN = os.path.expanduser('~/corsika-78010/run/CorsikaPlottermini')

_suffix = "_qgs" if MODEL == "qgs" else ""
THETAS = {0: f"out_0deg{_suffix}", 75: f"out_75deg{_suffix}"}

# primary energy grid: 10 GeV .. 1e5 GeV, 5 points per decade (21 points)
EMIN, EMAX, PTS_PER_DEC = 1e1, 1e5, 5
ndec = int(round(np.log10(EMAX / EMIN)))
npts = ndec * PTS_PER_DEC + 1
energies = np.logspace(np.log10(EMIN), np.log10(EMAX), npts)


def nshow_per_point(E):
    if E < 1e2:
        return 2000
    if E < 1e3:
        return 600
    if E < 1e4:
        return 200
    return 60


def make_card(theta, E, runnr, seed, nshow, outdir, path):
    if MODEL == "qgs":
        model_line = "QGSJET  T 0\nQGSSIG  T"
    else:
        model_line = "SIBYLL  T 0\nSIBSIG  T"
    card = f"""RUNNR   {runnr}
EVTNR   1
SEED    {seed} 0 0
SEED    {seed+1} 0 0
NSHOW   {nshow}
PRMPAR  14
ERANGE  {E:.6g} {E:.6g}
THETAP  {theta}. {theta}.
PHIP    -180. 180.
{model_line}
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
runnr = {"0": 1000 if MODEL == "sibyll" else 3000,
         "75": 2000 if MODEL == "sibyll" else 4000}
for theta, outname in THETAS.items():
    outdir = os.path.join(HERE, outname)
    os.makedirs(outdir, exist_ok=True)
    for i, E in enumerate(energies):
        nshow = nshow_per_point(E)
        seed = (300000 if MODEL == "sibyll" else 500000) + theta + i
        r = runnr[str(theta)] + i
        tag = f"{theta:02d}deg"
        card = os.path.join(CARDS, f"card_{tag}_E{i:02d}.inp")
        make_card(theta, E, r, seed, nshow, outdir, card)
        jobs.append((theta, E, r, seed, nshow, card, outdir))

jobs_path = os.path.join(HERE, f"jobs_{MODEL}.txt")
with open(jobs_path, "w") as f:
    f.write("# theta  E_gev  runnr  seed  nshow  card  outdir\n")
    for theta, E, r, seed, nshow, card, outdir in jobs:
        f.write(f"{theta}\t{E:.6g}\t{r}\t{seed}\t{nshow}\t{card}\t{outdir}\n")

total0 = sum(j[4] for j in jobs if j[0] == 0)
total75 = sum(j[4] for j in jobs if j[0] == 75)
print(f"Wrote {len(jobs)} jobs -> {jobs_path}")
print(f"  {len(energies)} energy points: {energies[0]:.4g} .. {energies[-1]:.4g} GeV")
print(f"  total showers: 0deg={total0}  75deg={total75}  (sum={total0+total75})")
