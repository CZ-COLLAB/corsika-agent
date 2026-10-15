#!/usr/bin/env python3
"""Analyze CORSIKA output files to reproduce ICRC 2021 Mars shower paper figures.

CORSIKA binary format (from corsikaread.f):
- Fortran sequential records, each 5733 floats (21 subblocks x 273 words)
- Subblock 1st word is marker: 'RUNH', 'EVTH', 'EVTE', 'RUNE', 'LONG' or 0 for DATA
- Particle data in DATA blocks: groups of 7 words per particle
  word[0]: encoded PID (idi/1000 = particle ID)
  word[1-3]: Px, Py, Pz (GeV/c)
  word[4-5]: X, Y (cm)
  word[6]: T (ns)
"""
import numpy as np
import os
import glob
import struct
import re
import sys
import warnings
warnings.filterwarnings('ignore')

def read_fortran_record(f):
    """Read a Fortran sequential record with C-style markers."""
    lead = f.read(4)
    if len(lead) < 4:
        return None
    rec_len = struct.unpack('<I', lead)[0]
    data = f.read(rec_len)
    if len(data) < rec_len:
        return None
    trail = f.read(4)
    return data

def get_marker(words, idx=0):
    """Get the 4-char marker from a float position."""
    v = words[idx]
    return struct.pack('<f', v)[:4]

def is_marker(words, marker, idx=0):
    """Check if word[idx] contains the given ASCII marker."""
    return get_marker(words, idx) == marker

def read_corsika_binary(filename, verbose=False):
    """Read CORSIKA binary file, extract events with particle positions.
    
    Returns list of dicts with event info and particle arrays.
    """
    f = open(filename, 'rb')
    events = []
    current_particles = []
    in_particle_data = False
    
    rec_num = 0
    while True:
        raw = read_fortran_record(f)
        if raw is None:
            break
        
        rec_num += 1
        n_words = len(raw) // 4
        floats = struct.unpack(f'<{n_words}f', raw)
        
        # Process 21 subblocks of 273 words each
        for sub in range(21):
            start = sub * 273
            if start + 273 > n_words:
                break
            subblock = floats[start:start+273]
            
            # Check marker
            marker_bytes = struct.pack('<f', subblock[0])[:4]
            
            if marker_bytes == b'RUNH':
                if verbose:
                    print(f"  Record {rec_num}, subblock {sub}: RUNH")
                in_particle_data = False
                
            elif marker_bytes == b'EVTH':
                if verbose:
                    print(f"  Record {rec_num}, subblock {sub}: EVTH (event start)")
                if current_particles:
                    events.append({
                        'particles': np.array(current_particles, dtype=[
                            ('pid', 'i4'), ('px', 'f4'), ('py', 'f4'), ('pz', 'f4'),
                            ('x', 'f4'), ('y', 'f4'), ('t', 'f4')
                        ]),
                    })
                    current_particles = []
                in_particle_data = True  # next non-header blocks are particle data
                # Also save event info
                # subblock[1]=event#, subblock[2]=primary, subblock[3]=energy
                
            elif marker_bytes == b'EVTE':
                if verbose:
                    print(f"  Record {rec_num}, subblock {sub}: EVTE (event end)")
                in_particle_data = False
                
            elif marker_bytes == b'RUNE':
                if verbose:
                    print(f"  Record {rec_num}, subblock {sub}: RUNE (run end)")
                in_particle_data = False
                
            elif marker_bytes[:3] == b'LON':
                if verbose:
                    print(f"  Record {rec_num}, subblock {sub}: LONG")
                in_particle_data = False
                
            elif in_particle_data:
                # Particle data block
                # Process in groups of 7
                for i in range(0, 273, 7):
                    if i + 7 > 273:
                        break
                    pid_encoded = int(subblock[i])
                    if pid_encoded == 0:
                        continue
                    pid = max(0, min(100, abs(pid_encoded) // 1000))
                    if pid <= 0 or pid > 200:
                        continue
                    px = subblock[i+1]
                    py = subblock[i+2]
                    pz = subblock[i+3]
                    x = subblock[i+4]
                    y = subblock[i+5]
                    t = subblock[i+6]
                    current_particles.append((pid, px, py, pz, x, y, t))
    
    # Add last event
    if current_particles:
        events.append({
            'particles': np.array(current_particles, dtype=[
                ('pid', 'i4'), ('px', 'f4'), ('py', 'f4'), ('pz', 'f4'),
                ('x', 'f4'), ('y', 'f4'), ('t', 'f4')
            ]),
        })
    
    f.close()
    if verbose:
        print(f"  Read {len(events)} events from {filename}")
    return events

def compute_longitudinal(filename_long):
    """Read longitudinal distribution file.
    Each event is stored sequentially starting with a header line
    'LONGITUDINAL DISTRIBUTION IN ... FOR SHOWER N'.
    Returns averaged depths and charged, plus total energy.
    """
    depths = None
    charged_sum = None
    n_events = 0
    total_energy = 0
    
    with open(filename_long, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i]
        if 'LONGITUDINAL DISTRIBUTION IN' in line and 'FOR SHOWER' in line:
            n_events += 1
            # Skip header and column header lines
            i += 2 if i+1 < len(lines) and 'DEPTH' in lines[i+1] else 1
            # Read data lines until energy deposit or fit
            event_charged = []
            event_depths = []
            while i < len(lines):
                line = lines[i]
                if 'LONGITUDINAL ENERGY DEPOSIT' in line or 'FIT OF THE HILLAS' in line:
                    break
                parts = line.split()
                if len(parts) >= 9:
                    try:
                        event_depths.append(float(parts[0]))
                        event_charged.append(float(parts[7]))
                    except:
                        pass
                i += 1
            
            if depths is None:
                depths = np.array(event_depths)
                charged_sum = np.array(event_charged, dtype=float)
            else:
                # Check same binning
                if len(event_depths) == len(depths):
                    charged_sum += np.array(event_charged)
                else:
                    # Different binning, interpolate or skip
                    pass
        else:
            # Check for ENERGY SUM line
            m = re.search(r'ENERGY SUM\s*=\s*([\d.E+\-]+)\s*GEV', line)
            if m:
                total_energy += float(m.group(1))
            i += 1
    
    if charged_sum is not None and n_events > 0:
        avg_charged = charged_sum / n_events
    else:
        avg_charged = np.array([])
    
    return depths, avg_charged, total_energy, n_events

def lateral_distribution(events, nbins=40, max_r=1e5):
    """Compute lateral distribution from particle data."""
    all_r = []
    all_pids = []
    
    for event in events:
        p = event['particles']
        if len(p) == 0:
            continue
        x = p['x']
        y = p['y']
        r = np.sqrt(x*x + y*y)
        all_r.extend(r.tolist())
        all_pids.extend(p['pid'].tolist())
    
    if not all_r:
        return np.array([]), np.array([]), np.array([]), np.array([]), np.array([])
    
    all_r = np.array(all_r)
    all_pids = np.array(all_pids)
    
    bins = np.logspace(np.log10(1), np.log10(max_r), nbins+1)
    bin_centers = np.sqrt(bins[:-1] * bins[1:])
    bin_widths = bins[1:] - bins[:-1]
    n_events = len(events)
    
    if n_events == 0:
        return bin_centers, np.zeros(nbins), np.zeros(nbins), np.zeros(nbins), np.zeros(nbins)
    
    # All charged (exclude gamma = 1)
    charged_mask = all_pids != 1
    counts, _ = np.histogram(all_r[charged_mask] if np.any(charged_mask) else np.array([]), bins=bins)
    charged_density = counts / bin_widths / n_events
    
    # Muons (5, 6)
    muon_mask = (all_pids == 5) | (all_pids == 6)
    muon_counts, _ = np.histogram(all_r[muon_mask] if np.any(muon_mask) else np.array([]), bins=bins)
    muon_density = muon_counts / bin_widths / n_events
    
    # Electrons (2, 3)
    emask = (all_pids == 2) | (all_pids == 3)
    e_counts, _ = np.histogram(all_r[emask] if np.any(emask) else np.array([]), bins=bins)
    e_density = e_counts / bin_widths / n_events
    
    # Gammas (1)
    gamma_counts, _ = np.histogram(all_r[all_pids == 1] if np.any(all_pids == 1) else np.array([]), bins=bins)
    gamma_density = gamma_counts / bin_widths / n_events
    
    return bin_centers, charged_density, muon_density, e_density, gamma_density

def analyze_run(run_dir, label, color, energy=1e5):
    """Analyze a CORSIKA run directory."""
    print(f"\n=== Analyzing {label} ({run_dir}) ===")
    
    long_files = sorted(glob.glob(os.path.join(run_dir, '*.long')))
    dat_files = sorted(glob.glob(os.path.join(run_dir, 'DAT*')))
    dat_files = [f for f in dat_files if not f.endswith('.long')]
    
    print(f"  Found {len(long_files)} .long files, {len(dat_files)} DAT files")
    
    # Combine longitudinal profiles
    all_depths = None
    all_charged = None
    n_events_long = 0
    total_energy = 0
    
    for lf in long_files:
        depths, avg_charged, e, nevt = compute_longitudinal(lf)
        if all_depths is None:
            all_depths = depths
            all_charged = avg_charged
        else:
            # Take first file's data (they should all be averaged same way)
            pass
        n_events_long += nevt
        total_energy += e
    
    avg_energy = total_energy / max(n_events_long, 1) if total_energy > 0 else 1e5
    print(f"  Longitudinal: {n_events_long} events, avg energy = {avg_energy:.1f} GeV")
    
    # Lateral distribution from DAT files
    all_events = []
    for df in dat_files[:50]:  # limit for testing
        try:
            evts = read_corsika_binary(df)
            all_events.extend(evts)
        except Exception as ex:
            print(f"  Error reading {df}: {ex}")
    
    print(f"  Total events for lateral: {len(all_events)}")
    
    if all_events:
        bin_centers, charged_density, muon_density, e_density, gamma_density = lateral_distribution(all_events)
    else:
        bin_centers = np.array([])
        charged_density = np.array([])
        muon_density = np.array([])
        e_density = np.array([])
        gamma_density = np.array([])
    
    return {
        'depths': all_depths,
        'charged': avg_charged,
        'n_events_long': n_events_long,
        'avg_energy': avg_energy,
        'r': bin_centers,
        'charged_density': charged_density,
        'muon_density': muon_density,
        'e_density': e_density,
        'gamma_density': gamma_density,
        'n_events_lat': len(all_events),
        'label': label,
        'color': color,
    }

def plot_results(results_list, output_prefix='result'):
    """Plot longitudinal and lateral profiles."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        # Longitudinal
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        for r in results_list:
            if len(r['depths']) > 0:
                ax.plot(r['depths'], r['charged'], '-o', color=r['color'], 
                       label=r['label'], markersize=3)
        ax.set_xlabel('Depth (g/cm²)')
        ax.set_ylabel('Charged particles')
        ax.set_yscale('log')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'{output_prefix}_longitudinal.png', dpi=150)
        print(f"Saved {output_prefix}_longitudinal.png")
        plt.close()
        
        # Lateral
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        for key, title, row, col in [
            ('charged_density', 'All Charged', 0, 0),
            ('muon_density', 'Muons', 0, 1),
            ('e_density', 'Electrons', 1, 0),
            ('gamma_density', 'Gammas', 1, 1),
        ]:
            ax = axes[row, col]
            for r in results_list:
                if len(r['r']) > 0 and len(r[key]) > 0:
                    ax.plot(r['r'], r[key], '-', color=r['color'], label=r['label'])
            ax.set_xlabel('r (cm)')
            ax.set_ylabel('density (particles/cm)')
            ax.set_xscale('log')
            ax.set_yscale('log')
            ax.set_title(title)
            ax.legend()
            ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'{output_prefix}_lateral.png', dpi=150)
        print(f"Saved {output_prefix}_lateral.png")
        plt.close()
        
    except Exception as e:
        print(f"Plotting error: {e}")

if __name__ == '__main__':
    mars_dir = sys.argv[1] if len(sys.argv) > 1 else 'Mars_results'
    earth_dir = sys.argv[2] if len(sys.argv) > 2 else 'Earth_results'
    
    mars = analyze_run(mars_dir, 'Mars', 'red')
    earth = analyze_run(earth_dir, 'Earth', 'blue')
    
    plot_results([mars, earth])
    print("\nDone!")
