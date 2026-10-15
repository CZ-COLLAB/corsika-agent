#!/usr/bin/env python3
"""Convert my CORSIKA flux (per kinetic energy) into the CRY C-code data-array
format (7 columns, per momentum dN/dp), matching the user's bin grid.

Bin grid: p_edge = 0.1 * 10^(0.15 * i), i = 0..40  (40 bins, 0.1 .. 100000 GeV/c)
Columns: { p_center (arith mean), p_low, p_high, dN/dp, abs_err, rel_err, width }
"""
import numpy as np

MUON_MASS = 0.105658

# user's bin grid
edges = 0.1 * 10.0**(0.15 * np.arange(41))
low, high = edges[:-1], edges[1:]
center = (low + high) / 2.0
width = high - low
n = len(center)

def load(theta):
    d = np.loadtxt(f"results/flux_{theta}deg.csv", skiprows=1)
    E, I, s = d[:,0], d[:,1], d[:,2]   # kinetic energy, dN/dE_kin, sigma
    p = np.sqrt(E*E + 2*MUON_MASS*E)   # kinetic E -> momentum
    dpdE = p / (E + MUON_MASS)         # dp/dE_kin = p/E_total
    # dN/dp = dN/dE_kin * dE_kin/dp = I / dpdE
    dndp = I / dpdE
    sdndp = s / dpdE
    return p, dndp, sdndp

def interp_log(xs, ys, xtarget):
    lx = np.log(xs); lxt = np.log(xtarget)
    return np.interp(lxt, lx, ys)

def emit(theta, label):
    p, dndp, sdndp = load(theta)
    flux = interp_log(p, dndp, center)
    sig  = interp_log(p, sdndp, center)
    # zero out regions with no data (outside my momentum range)
    valid = (center >= p.min()) & (center <= p.max())
    flux = np.where(valid, flux, 0.0)
    sig  = np.where(valid, sig, 0.0)
    rel = np.where(flux > 0, sig/flux, 0.0)

    name = f"corsika_data_urqmd_agent_{theta}deg"
    print(f"\n// ==================== Agent generated (SIBYLL+urqmd, {theta}deg) ====================")
    print(f"double {name}[{n}][7] = {{")
    for i in range(n):
        print(f"    {{{center[i]:.6e}, {low[i]:.6e}, {high[i]:.6e}, "
              f"{flux[i]:.6e}, {sig[i]:.6e}, {rel[i]:.6e}, {width[i]:.6e}}},")
    print("};")

if __name__ == "__main__":
    emit(0, "0deg")
    emit(75, "75deg")
