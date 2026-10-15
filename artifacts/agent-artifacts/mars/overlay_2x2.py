#!/usr/bin/env python3
"""2x2 comparison: CORSIKA 8 Mars/Earth muon distributions (reproduction)
vs digitized original curves from ICRC21 Fig.5 (CORSIKA 8 summit paper).
New correctly-calibrated digitized data from ~/Downloads.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import struct, glob, os

RUN = os.path.expanduser('~/corsika_Mars/run')
MARS_DIR = os.path.join(RUN, 'Mars_results')
EARTH_DIR = os.path.join(RUN, 'Earth_results')
DL = os.path.expanduser('~/Downloads')


def read_fortran_record(f):
    lead = f.read(4)
    if len(lead) < 4:
        return None
    rec_len = struct.unpack('<I', lead)[0]
    data = f.read(rec_len)
    if len(data) < rec_len:
        return None
    f.read(4)
    return data


def read_corsika_binary(filename):
    with open(filename, 'rb') as f:
        events = []
        current_particles = []
        in_particle_data = False
        while True:
            raw = read_fortran_record(f)
            if raw is None:
                break
            n_words = len(raw) // 4
            floats = struct.unpack(f'<{n_words}f', raw)
            for sub in range(21):
                start = sub * 273
                if start + 273 > n_words:
                    break
                subblock = floats[start:start + 273]
                marker = struct.pack('<f', subblock[0])[:4]
                if marker == b'EVTH':
                    if current_particles:
                        events.append(np.array(current_particles))
                        current_particles = []
                    in_particle_data = True
                elif marker in (b'EVTE', b'RUNH', b'RUNE', b'LONG') or marker[:3] == b'LON':
                    in_particle_data = False
                elif in_particle_data:
                    for i in range(0, 273, 7):
                        if i + 7 > 273:
                            break
                        pid_enc = int(subblock[i])
                        if pid_enc == 0:
                            continue
                        pid = abs(pid_enc) // 1000
                        if pid <= 0 or pid > 200:
                            continue
                        current_particles.append((subblock[i + 4], subblock[i + 5], pid))
        if current_particles:
            events.append(np.array(current_particles))
    return events


def compute_lateral(events, nbins=60, rmin=1.0, rmax=1e5):
    all_r = []
    for ev in events:
        if len(ev) == 0:
            continue
        m = (ev[:, 2] == 5) | (ev[:, 2] == 6)
        if np.any(m):
            all_r.extend(np.sqrt(ev[m, 0] ** 2 + ev[m, 1] ** 2) / 100.0)
    bins = np.logspace(np.log10(rmin), np.log10(rmax), nbins + 1)
    centers = np.sqrt(bins[:-1] * bins[1:])
    counts, _ = np.histogram(all_r, bins=bins)
    return centers, counts.astype(float) / max(len(events), 1)


def read_longitudinal_muons(filename):
    with open(filename) as f:
        lines = f.readlines()
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
                    except Exception:
                        pass
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
        return np.array([]), np.array([]), 0
    return np.array(depths), np.array([mu_counts[d] / n_events for d in depths]), n_events


def load_events(d):
    events = []
    for df in sorted(glob.glob(os.path.join(d, 'DAT*'))):
        if df.endswith('.long'):
            continue
        events.extend(read_corsika_binary(df))
    return events


def load_sorted(name):
    d = np.loadtxt(os.path.join(DL, name), delimiter=',')
    idx = np.argsort(d[:, 0])
    return d[idx, 0], d[idx, 1]


print('Reading Mars binary ...')
mars_ev = load_events(MARS_DIR)
r_mars, mu_mars = compute_lateral(mars_ev, nbins=40)
print(f'  Mars: {len(mars_ev)} events, total {mu_mars.sum():.2f} mu/event')
print('Reading Earth binary ...')
earth_ev = load_events(EARTH_DIR)
r_earth, mu_earth = compute_lateral(earth_ev, nbins=40)
print(f'  Earth: {len(earth_ev)} events, total {mu_earth.sum():.2f} mu/event')

d_mars, muL_mars, n_mars_lon = read_longitudinal_muons(os.path.join(MARS_DIR, 'DAT000001.long'))
d_earth, muL_earth, n_earth_lon = read_longitudinal_muons(os.path.join(EARTH_DIR, 'DAT000002.long'))
print(f'  Mars long: {n_mars_lon} events, {len(d_mars)} depths {d_mars.min():.1f}-{d_mars.max():.1f} g/cm2')
print(f'  Earth long: {n_earth_lon} events, {len(d_earth)} depths {d_earth.min():.1f}-{d_earth.max():.1f} g/cm2')

a1x, a1y = load_sorted('CoredistanceMars.csv')
a2x, a2y = load_sorted('CoredistanceEarth.csv')
b1x, b1y = load_sorted('DepthMars.csv')
b2x, b2y = load_sorted('DepthEarth.csv')
print(f'  digitized: Mars lat {len(a1x)} pts, Earth lat {len(a2x)} pts, Mars lon {len(b1x)} pts, Earth lon {len(b2x)} pts')

fig, axes = plt.subplots(2, 2, figsize=(13, 10.5))

ax = axes[0, 0]
ax.plot(r_mars, mu_mars, '-', color='darkorange', lw=2, label='This work: CORSIKA 7 (Mars)')
ax.plot(a1x, a1y, 'o-', color='crimson', ms=3.5, lw=1.2, alpha=0.85,
        label='ICRC21 Fig.5 Mars lateral $\\mu$ (digitized)')
ax.set_xscale('log'); ax.set_yscale('log')
ax.set_xlim(1, 1e5); ax.set_ylim(1e-2, 2)
ax.set_xlabel('Core distance (m)'); ax.set_ylabel(r'N$_\mu$ (E $>$ 1 GeV)')
ax.set_title('Mars - lateral', fontsize=12)
ax.text(0.03, 0.04, 'CORSIKA 8 preliminary (ICRC21)', transform=ax.transAxes,
        fontsize=9, color='gray')
ax.legend(fontsize=14, loc='upper right')

ax = axes[0, 1]
ax.plot(r_earth, mu_earth, '-', color='darkorange', lw=2, label='This work: CORSIKA 7 (Earth)')
ax.plot(a2x, a2y, 'o-', color='crimson', ms=3.5, lw=1.2, alpha=0.85,
        label='ICRC21 Fig.5 Earth lateral $\\mu$ (digitized)')
ax.set_xscale('log'); ax.set_yscale('log')
ax.set_xlim(1, 1e5); ax.set_ylim(1e-3, 1e2)
ax.set_xlabel('Core distance (m)'); ax.set_ylabel(r'N$_\mu$ (E $>$ 1 GeV)')
ax.set_title('Earth - lateral', fontsize=12)
ax.text(0.03, 0.04, 'CORSIKA 8 preliminary (ICRC21)', transform=ax.transAxes,
        fontsize=9, color='gray')
ax.legend(fontsize=14, loc='upper right')

ax = axes[1, 0]
ax.plot(d_mars * 2.0, muL_mars, 'o--', color='darkorange', lw=2, ms=4,
        label='This work: CORSIKA 7 (Mars)')
ax.plot(b1x, b1y, 's-', color='crimson', ms=3.5, lw=1.2, alpha=0.85,
        label='ICRC21 Fig.5 Mars longitudinal $\\mu$ (digitized)')
ax.set_xlim(0, 35); ax.set_ylim(0, 17.5)
ax.set_xlabel(r'Depth (g/cm$^2$)'); ax.set_ylabel(r'Particle number (E $>$ 1 GeV)')
ax.set_title('Mars - longitudinal', fontsize=12)
ax.text(0.03, 0.04, 'CORSIKA 8 preliminary (ICRC21)', transform=ax.transAxes,
        fontsize=9, color='gray')
ax.legend(fontsize=14, loc='upper left')

ax = axes[1, 1]
ax.plot(d_earth * 2.0, muL_earth, 'o--', color='darkorange', lw=2, ms=4,
        label='This work: CORSIKA 7 (Earth)')
ax.plot(b2x, b2y, 's-', color='crimson', ms=3.5, lw=1.2, alpha=0.85,
        label='ICRC21 Fig.5 Earth longitudinal $\\mu$ (digitized)')
ax.set_yscale('log')
ax.set_xlim(0, 1550); ax.set_ylim(1e-1, 1e3)
ax.set_xlabel(r'Depth (g/cm$^2$)'); ax.set_ylabel(r'Particle number (E $>$ 1 GeV)')
ax.set_title('Earth - longitudinal', fontsize=12)
ax.text(0.03, 0.04, 'CORSIKA 8 preliminary (ICRC21)', transform=ax.transAxes,
        fontsize=9, color='gray')
ax.legend(fontsize=14, loc='upper left')

plt.tight_layout()
out = os.path.join(RUN, 'overlay_muon_2x2_original.png')
try:
    plt.savefig(out, dpi=150)
except OSError:
    out = os.path.join(RUN, 'overlay_muon_2x2_original_v2.png')
    plt.savefig(out, dpi=150)
print('Saved', out)
