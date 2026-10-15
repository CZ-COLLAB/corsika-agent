#!/usr/bin/env python3
"""Plot muon lateral + longitudinal 2×2 figure for ICRC21 paper reproduction."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import struct, os, glob, re, sys

def read_fortran_record(f):
    lead = f.read(4)
    if len(lead) < 4: return None
    rec_len = struct.unpack('<I', lead)[0]
    data = f.read(rec_len)
    if len(data) < rec_len: return None
    f.read(4)
    return data

def read_corsika_binary(filename):
    """Read events from CORSIKA DAT, return list of (x_cm, y_cm, pid) arrays."""
    with open(filename, 'rb') as f:
        events = []
        current_particles = []
        in_particle_data = False
        while True:
            raw = read_fortran_record(f)
            if raw is None: break
            n_words = len(raw) // 4
            floats = struct.unpack(f'<{n_words}f', raw)
            for sub in range(21):
                start = sub * 273
                if start + 273 > n_words: break
                subblock = floats[start:start+273]
                marker = struct.pack('<f', subblock[0])[:4]
                if marker == b'EVTH':
                    if current_particles:
                        events.append(np.array(current_particles))
                        current_particles = []
                    in_particle_data = True
                elif marker == b'EVTE':
                    in_particle_data = False
                elif marker in (b'RUNH', b'RUNE', b'LONG'):
                    in_particle_data = False
                elif marker[:3] == b'LON':
                    in_particle_data = False
                elif in_particle_data:
                    for i in range(0, 273, 7):
                        if i + 7 > 273: break
                        pid_enc = int(subblock[i])
                        if pid_enc == 0: continue
                        pid = abs(pid_enc) // 1000
                        if pid <= 0 or pid > 200: continue
                        current_particles.append((
                            subblock[i+4], subblock[i+5],  # x, y (cm)
                            pid
                        ))
        if current_particles:
            events.append(np.array(current_particles))
    return events

def read_longitudinal_muons(filename):
    """Read MU+ and MU- columns from .long file per depth, return averaged arrays."""
    with open(filename) as f:
        lines = f.readlines()
    depth_values = None
    depth_set = set()
    mu_counts = None
    n_events = 0
    for i, line in enumerate(lines):
        if 'LONGITUDINAL DISTRIBUTION IN' in line and 'FOR SHOWER' in line:
            n_events += 1
            event_mu = {}
            i2 = i + 2
            while i2 < len(lines):
                l = lines[i2]
                if 'LONGITUDINAL ENERGY DEPOSIT' in l or 'FIT OF THE HILLAS' in l:
                    break
                parts = l.split()
                if len(parts) >= 6:
                    try:
                        d = float(parts[0])
                        mup = float(parts[4])
                        mum = float(parts[5])
                        event_mu[d] = mup + mum
                    except: pass
                i2 += 1
            for d, c in event_mu.items():
                depth_set.add(d)
            if mu_counts is None:
                mu_counts = event_mu
            else:
                for d, c in event_mu.items():
                    mu_counts[d] = mu_counts.get(d, 0) + c
    depths = sorted(depth_set)
    if mu_counts is None or n_events == 0:
        return np.array([]), np.array([])
    return np.array(depths), np.array([mu_counts[d] / n_events for d in depths])

def compute_lateral_from_binary(events, nbins=60, rmin=1.0, rmax=1e5):
    """Compute muon lateral distribution from binary data.
    Returns bin_centers (m) and muon_counts (particles/event per radial bin).
    """
    all_r_mu = []
    for ev in events:
        if len(ev) == 0: continue
        x = ev[:, 0]
        y = ev[:, 1]
        pids = ev[:, 2]
        mu_mask = (pids == 5) | (pids == 6)
        if np.any(mu_mask):
            r_m = np.sqrt(x[mu_mask]**2 + y[mu_mask]**2) / 100.0
            all_r_mu.extend(r_m)

    if not all_r_mu: return np.array([]), np.array([])

    bins = np.logspace(np.log10(rmin), np.log10(rmax), nbins + 1)
    bin_centers = np.sqrt(bins[:-1] * bins[1:])
    counts, _ = np.histogram(all_r_mu, bins=bins)
    counts_per_event = counts.astype(float) / max(len(events), 1)
    return bin_centers, counts_per_event

mars_dir = sys.argv[1] if len(sys.argv) > 1 else 'Mars_results'
earth_dir = sys.argv[2] if len(sys.argv) > 2 else 'Earth_results'

print("Reading Mars binary...")
mars_events = []
for df in sorted(glob.glob(os.path.join(mars_dir, 'DAT*'))):
    if df.endswith('.long'): continue
    mars_events.extend(read_corsika_binary(df))
print(f"  {len(mars_events)} events")

print("Reading Earth binary...")
earth_events = []
for df in sorted(glob.glob(os.path.join(earth_dir, 'DAT*'))):
    if df.endswith('.long'): continue
    earth_events.extend(read_corsika_binary(df))
print(f"  {len(earth_events)} events")

print("Reading Mars longitudinal...")
mars_long_files = sorted(glob.glob(os.path.join(mars_dir, '*.long')))
mars_depths, mars_mu_avg = np.array([]), np.array([])
for lf in mars_long_files:
    d, m = read_longitudinal_muons(lf)
    if len(d) > len(mars_depths):
        mars_depths, mars_mu_avg = d, m

print("Reading Earth longitudinal...")
earth_long_files = sorted(glob.glob(os.path.join(earth_dir, '*.long')))
earth_depths, earth_mu_avg = np.array([]), np.array([])
for lf in earth_long_files:
    d, m = read_longitudinal_muons(lf)
    if len(d) > len(earth_depths):
        earth_depths, earth_mu_avg = d, m

print(f"Mars: {len(mars_depths)} depth bins, Earth: {len(earth_depths)} depth bins")

print("Computing lateral distributions...")
mars_r, mars_mu_lat = compute_lateral_from_binary(mars_events)
earth_r, earth_mu_lat = compute_lateral_from_binary(earth_events)

print(f"\nMars lateral: {len(mars_r)} bins, Earth lateral: {len(earth_r)} bins")

fig, axes = plt.subplots(2, 2, figsize=(12, 8))

# Top-left: Mars lateral
ax = axes[0, 0]
if len(mars_r) > 0:
    ax.plot(mars_r, mars_mu_lat, '-', color='darkorange', linewidth=2, label=r'$\mu^\pm$')
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlim(1, 1e5)
ax.set_ylim(1e-2, 1e0)
ax.set_xlabel('Core distance (m)', fontsize=11)
ax.set_ylabel(r'N$_{\mathrm{part}}$ (E $>$ 1 GeV)', fontsize=11)
ax.text(0.03, 0.96, 'CORSIKA 8 preliminary (ICRC21)', transform=ax.transAxes,
        fontsize=8, va='top', ha='left', style='italic')
ax.text(0.85, 0.88, 'Mars', transform=ax.transAxes, fontsize=16,
        va='top', ha='center', fontweight='bold')
ax.legend(fontsize=10, loc='upper right')
ax.grid(True, alpha=0.3, which='both')

# Top-right: Earth lateral
ax = axes[0, 1]
if len(earth_r) > 0:
    ax.plot(earth_r, earth_mu_lat, '-', color='darkorange', linewidth=2, label=r'$\mu^\pm$')
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlim(1, 1e5)
ax.set_ylim(1e-3, 1e1)
ax.set_xlabel('Core distance (m)', fontsize=11)
ax.set_ylabel(r'N$_{\mathrm{part}}$ (E $>$ 1 GeV)', fontsize=11)
ax.text(0.03, 0.96, 'CORSIKA 8 preliminary (ICRC21)', transform=ax.transAxes,
        fontsize=8, va='top', ha='left', style='italic')
ax.text(0.85, 0.88, 'Earth', transform=ax.transAxes, fontsize=16,
        va='top', ha='center', fontweight='bold')
ax.legend(fontsize=10, loc='upper right')
ax.grid(True, alpha=0.3, which='both')

# Bottom-left: Mars longitudinal
ax = axes[1, 0]
if len(mars_depths) > 0:
    ax.plot(mars_depths, mars_mu_avg, '--', color='darkorange', linewidth=2, label=r'$\mu^\pm$')
ax.set_xlim(0, 35)
ax.set_ylim(0, 17.5)
ax.set_xlabel('Depth (g/cm²)', fontsize=11)
ax.set_ylabel('Particle number (E $>$ 1 GeV)', fontsize=11)
ax.text(0.03, 0.96, 'CORSIKA 8 preliminary (ICRC21)', transform=ax.transAxes,
        fontsize=8, va='top', ha='left', style='italic')
ax.text(0.85, 0.88, 'Mars', transform=ax.transAxes, fontsize=16,
        va='top', ha='center', fontweight='bold')
ax.legend(fontsize=10, loc='upper left')
ax.grid(True, alpha=0.3)

# Bottom-right: Earth longitudinal
ax = axes[1, 1]
if len(earth_depths) > 0:
    ax.plot(earth_depths, earth_mu_avg, '-', color='darkorange', linewidth=2, label=r'$\mu^\pm$')
ax.set_xlim(0, 1500)
ax.set_ylim(1e-1, 1e3)
ax.set_yscale('log')
ax.set_xlabel('Depth (g/cm²)', fontsize=11)
ax.set_ylabel('Particle number (E $>$ 1 GeV)', fontsize=11)
ax.text(0.03, 0.96, 'CORSIKA 8 preliminary (ICRC21)', transform=ax.transAxes,
        fontsize=8, va='top', ha='left', style='italic')
ax.text(0.85, 0.88, 'Earth', transform=ax.transAxes, fontsize=16,
        va='top', ha='center', fontweight='bold')
ax.legend(fontsize=10, loc='upper right')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('muon_2x2.png', dpi=150)
print("Saved muon_2x2.png")
plt.close()
