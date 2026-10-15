#!/usr/bin/env python3
"""Generate steering cards for ISOTROPIC primary injection (THETAP 0 89).

Cosmic rays are isotropic; instead of injecting at a fixed zenith angle, inject
primaries over the full 0-89 deg range (flat-detector isotropic sampling, i.e.
CORSIKA samples sin(theta)*cos(theta)), then select muons in angular bins in the
analysis.  Single run covers both the vertical (0-5 deg) and 75 deg (70-80 deg)
bins.
"""
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CARDS = os.path.join(HERE, "cards")
os.makedirs(CARDS, exist_ok=True)

CORSIKA_BIN = os.path.expanduser('~/corsika-78010/run/corsika78010Linux_SIBYLL_urqmd')

# proton total-energy grid (same as before): 10 GeV .. 1e5 GeV, 5/decade
EMIN, EMAX, PTS = 1e1, 1e5, 5
ndec = int(round(np.log10(EMAX / EMIN)))
npts = ndec * PTS + 1
energies = np.logspace(np.log10(EMIN), np.log10(EMAX), npts)


def nshow_per_point(E):
    if E < 1e2:
        return 50000
    if E < 1e3:
        return 15000
    if E < 1e4:
        return 5000
    return 300


OUTDIR = os.path.join(HERE, "out_iso")

jobs = []
for i, E in enumerate(energies):
    nshow = nshow_per_point(E)
    seed = 900000 + i
    r = 8000 + i
    card = os.path.join(CARDS, f"card_iso_E{i:02d}.inp")
    with open(card, "w") as f:
        f.write(f"""RUNNR   {r}
EVTNR   1
SEED    {seed} 0 0
SEED    {seed+1} 0 0
NSHOW   {nshow}
PRMPAR  14
ERANGE  {E:.6g} {E:.6g}
THETAP  0. 89.
PHIP    -180. 180.
SIBYLL  T 0
SIBSIG  T
URQMD   T 0
ELMFLG  T T
ECUTS   0.3  0.3  0.003 0.003
OBSLEV  0.
MAGNET  20.40 43.23
PAROUT  T F
DIRECT  {OUTDIR}/
EXIT
""")
    jobs.append((E, r, seed, nshow, card))

jobs_path = os.path.join(HERE, "jobs_iso.txt")
with open(jobs_path, "w") as f:
    f.write("# E_gev  runnr  seed  nshow  card\n")
    for E, r, seed, nshow, card in jobs:
        f.write(f"{E:.6g}\t{r}\t{seed}\t{nshow}\t{card}\n")

print(f"Wrote {len(jobs)} isotropic jobs -> {jobs_path}")
print(f"  total showers: {sum(j[3] for j in jobs)}")
