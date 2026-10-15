#!/usr/bin/env python3
"""Aggregate the fixed-angle CORSIKA runs into the muon flux vs zenith angle
(relative, spectrum-reweighted) for the Cohu et al. Fig.2 reproduction.

Sampling: CORSIKA ESLOPE = -1.7 (importance sampling, flatter than reality).
True primary differential spectrum assumed dN/dE ~ E^-2.7, so each event is
weighted by w(E) = E^(-2.7) / E^(-1.7) = E^(-1.0).

I(theta) = (1/Nshow) * sum_i w(E_i) * N_mu,i        [arbitrary units]
Error from the weighted scatter (delta method / bootstrap).
"""
import glob
import os
import re
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from analyze import parse_events  # noqa: E402

SAMPLING_SLOPE = -1.7
TRUE_SLOPE = -2.7


def weight(e):
    return np.power(e, TRUE_SLOPE - SAMPLING_SLOPE)


def process(datfile):
    ev = parse_events(datfile)
    n = len(ev)
    w = np.array([weight(e['eprim']) for e in ev])
    nmu = np.array([sum(1 for p in e['parts'] if int(p[0] / 1000) in (5, 6))
                    for e in ev])
    if n == 0:
        return None
    prod = w * nmu
    I = prod.sum() / n
    # standard error of the mean of w*N
    if n > 1:
        err = prod.std(ddof=1) / np.sqrt(n)
    else:
        err = 0.0
    return dict(nshow=n, nmu_total=int(nmu.sum()), I=I, err=err,
                wsum=w.sum(), nmu_unweighted=nmu.mean(),
                emin=min(e['eprim'] for e in ev), emax=max(e['eprim'] for e in ev))


def main():
    pat = os.path.join(HERE, 'out', 'DAT*')
    rows = []
    for f in sorted(glob.glob(pat)):
        base = os.path.basename(f)
        if base.endswith(('.tab', '.root')):
            continue
        m = re.search(r'corsika_theta([\d.]+)\.lst', '')
        # theta is encoded in the run number list below
        rows.append(f)
    # map run number -> theta from the inp files
    run2theta = {}
    for inp in glob.glob(os.path.join(HERE, 'out', 'inp_theta*.inp')):
        th = re.search(r'inp_theta([\d.]+)\.inp', inp).group(1)
        for line in open(inp):
            if line.startswith('RUNNR'):
                run2theta[int(line.split()[1])] = float(th)
    out = []
    for f in glob.glob(os.path.join(HERE, 'out', 'DAT*')):
        base = os.path.basename(f)
        if base.endswith(('.tab', '.root')):
            continue
        mm = re.match(r'DAT(\d+)$', base)
        if not mm:
            continue
        run = int(mm.group(1))
        if run not in run2theta:
            continue
        r = process(f)
        if r is None:
            continue
        r['theta'] = run2theta[run]
        r['run'] = run
        r['file'] = base
        out.append(r)
    out.sort(key=lambda d: d['theta'])
    print(f"{'theta':>6} {'Nshow':>7} {'Nmu':>8} {'<Nmu>':>9} "
          f"{'I(rel)':>12} {'err':>11} {'Emin':>8} {'Emax':>9}")
    for r in out:
        print(f"{r['theta']:6.1f} {r['nshow']:7d} {r['nmu_total']:8d} "
              f"{r['nmu_unweighted']:9.3f} {r['I']:12.5e} {r['err']:11.3e} "
              f"{r['emin']:8.1f} {r['emax']:9.1f}")
    np.save(os.path.join(HERE, 'scan_result.npy'), out)


if __name__ == '__main__':
    main()
