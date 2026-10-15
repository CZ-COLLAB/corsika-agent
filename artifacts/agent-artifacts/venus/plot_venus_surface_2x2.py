#!/usr/bin/env python3
"""Venus surface vs Earth sea level muon 2x2, following overlay_2x2.py standard.

Uses the 3000-event Venus surface run (venus_surf_results_3k) for better
lateral statistics. Venus lateral r-range narrowed to ~1 km (muons are all
absorbed beyond ~700 m in the 100x-thicker atmosphere).

Convention (from overlay_2x2.py): lateral = counts/event per radial bin (NOT
divided by annulus area); longitudinal = mu+ + mu- summed per depth, averaged
over events. Slant depth = vertical depth * 2.0 (60 deg).
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import struct, glob, os

RUN = os.path.expanduser('~/corsika_Mars/run')
VENUS_DIR = os.path.join(RUN, 'venus_surf_results_3k')
EARTH_DIR = os.path.join(RUN, 'Earth_results')


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
    events = []
    current_particles = []
    in_particle_data = False
    seen_evth = False
    with open(filename, 'rb') as f:
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
                    if seen_evth:
                        events.append(np.array(current_particles))
                        current_particles = []
                    seen_evth = True
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
        if seen_evth:
            events.append(np.array(current_particles))
    return events


def compute_lateral(events, nbins=40, rmin=1.0, rmax=1e5):
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
    """Streaming reader: sum mu+ + mu- per depth over events, average."""
    depth_set = set()
    mu_counts = {}
    n_events = 0
    with open(filename) as f:
        in_block = False
        event_mu = {}
        for line in f:
            if 'LONGITUDINAL DISTRIBUTION IN' in line and 'FOR SHOWER' in line:
                n_events += 1
                if event_mu:
                    for d, c in event_mu.items():
                        depth_set.add(d)
                        mu_counts[d] = mu_counts.get(d, 0) + c
                event_mu = {}
                in_block = True
                continue
            if 'LONGITUDINAL ENERGY DEPOSIT' in line or 'FIT OF THE HILLAS' in line:
                in_block = False
                continue
            if in_block:
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        d = float(parts[0])
                        event_mu[d] = event_mu.get(d, 0) + float(parts[4]) + float(parts[5])
                    except Exception:
                        pass
        if event_mu:
            for d, c in event_mu.items():
                depth_set.add(d)
                mu_counts[d] = mu_counts.get(d, 0) + c
    depths = sorted(depth_set)
    if not depths or n_events == 0:
        return np.array([]), np.array([]), 0
    return np.array(depths), np.array([mu_counts[d] / n_events for d in depths]), n_events


def load_events(d):
    events = []
    for df in sorted(glob.glob(os.path.join(d, 'DAT*'))):
        if df.endswith('.long'):
            continue
        events.extend(read_corsika_binary(df))
    return events


print('Reading Venus surface binary (3000 events) ...')
venus_ev = load_events(VENUS_DIR)
r_venus, mu_venus = compute_lateral(venus_ev, nbins=12, rmin=10.0, rmax=1e3)
nmu_v = sum(1 for e in venus_ev for p in e if p[2] in (5, 6))
print(f'  Venus: {len(venus_ev)} events, total {nmu_v} mu, mu/event={nmu_v/len(venus_ev):.3f}')

print('Reading Earth binary ...')
earth_ev = load_events(EARTH_DIR)
r_earth, mu_earth = compute_lateral(earth_ev, nbins=40, rmin=1.0, rmax=1e5)
nmu_e = sum(1 for e in earth_ev for p in e if p[2] in (5, 6))
print(f'  Earth: {len(earth_ev)} events, total {nmu_e} mu, mu/event={nmu_e/len(earth_ev):.3f}')

print('Reading Venus longitudinal (streaming, large .long) ...')
d_venus, muL_venus, n_v = read_longitudinal_muons(os.path.join(VENUS_DIR, 'DAT000001.long'))
print('Reading Earth longitudinal ...')
d_earth, muL_earth, n_e = read_longitudinal_muons(os.path.join(EARTH_DIR, 'DAT000002.long'))
print(f'  Venus long: {n_v} events, depths {d_venus.min():.1f}-{d_venus.max():.1f}, max mu {muL_venus.max():.1f}')
print(f'  Earth long: {n_e} events, depths {d_earth.min():.1f}-{d_earth.max():.1f}, max mu {muL_earth.max():.1f}')

fig, axes = plt.subplots(2, 2, figsize=(13, 10.5))

ax = axes[0, 0]
ax.plot(r_venus, mu_venus, '-', color='darkorange', lw=2, label='This work: CORSIKA 7 (Venus surface)')
ax.set_xscale('log'); ax.set_yscale('log')
ax.set_xlim(10, 1e3); ax.set_ylim(1e-3, 1e0)
ax.set_xlabel('Core distance (m)'); ax.set_ylabel(r'N$_\mu$ (E $>$ 1 GeV)')
ax.set_title('Venus surface - lateral', fontsize=12)
ax.legend(fontsize=13, loc='upper right')

ax = axes[0, 1]
ax.plot(r_earth, mu_earth, '-', color='darkorange', lw=2, label='This work: CORSIKA 7 (Earth sea level)')
ax.set_xscale('log'); ax.set_yscale('log')
ax.set_xlim(1, 1e5); ax.set_ylim(1e-3, 1e2)
ax.set_xlabel('Core distance (m)'); ax.set_ylabel(r'N$_\mu$ (E $>$ 1 GeV)')
ax.set_title('Earth sea level - lateral', fontsize=12)
ax.legend(fontsize=13, loc='upper right')

ax = axes[1, 0]
ax.plot(d_venus * 2.0, muL_venus, 'o--', color='darkorange', lw=2, ms=4,
        label='This work: CORSIKA 7 (Venus)')
ax.set_yscale('log')
ax.set_xlim(0, 2.2e5); ax.set_ylim(1e-1, 1e3)
ax.set_xlabel(r'Depth (g/cm$^2$)'); ax.set_ylabel(r'Particle number (E $>$ 1 GeV)')
ax.set_title('Venus surface - longitudinal', fontsize=12)
ax.legend(fontsize=13, loc='upper right')

ax = axes[1, 1]
ax.plot(d_earth * 2.0, muL_earth, 'o--', color='darkorange', lw=2, ms=4,
        label='This work: CORSIKA 7 (Earth)')
ax.set_yscale('log')
ax.set_xlim(0, 2500); ax.set_ylim(1e-1, 1e3)
ax.set_xlabel(r'Depth (g/cm$^2$)'); ax.set_ylabel(r'Particle number (E $>$ 1 GeV)')
ax.set_title('Earth sea level - longitudinal', fontsize=12)
ax.legend(fontsize=13, loc='upper right')

plt.tight_layout()
out = os.path.join(RUN, 'venus', 'venus_vs_earth_surface_2x2.png')
plt.savefig(out, dpi=150)
plt.savefig(out.replace('.png', '.pdf'))
print('Saved', out)
