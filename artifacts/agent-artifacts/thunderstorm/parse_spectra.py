#!/usr/bin/env python3
"""Parse CORSIKA DAT files into kinetic-energy arrays (cached)."""
import struct, os, sys
import numpy as np

MASS = {1:0.0, 2:0.000511, 3:0.000511, 5:0.105658, 6:0.105658,
        13:0.13957, 14:0.13957}

def read_blocks(fname):
    chunks = []
    with open(fname, 'rb') as f:
        while True:
            hdr = f.read(4)
            if len(hdr) < 4:
                break
            l1 = struct.unpack('<i', hdr)[0]
            blk = f.read(l1)
            if len(blk) < l1:
                break
            f.read(4)
            chunks.append(blk)
    return b''.join(chunks)

def parse_showers(fname):
    block = read_blocks(fname)
    nw = len(block) // 4
    F4 = struct.Struct('<f'); I4 = struct.Struct('<i')
    def fw(w): return F4.unpack_from(block, w*4)[0]
    def iw(w): return I4.unpack_from(block, w*4)[0]
    def mk(w): return block[w*4:w*4+4]
    evth = sorted([i for i in range(nw) if i % 273 == 0 and mk(i) == b'EVTH'])
    evte = sorted([i for i in range(nw) if i % 273 == 0 and mk(i) == b'EVTE'])
    showers = []
    for h in evth:
        cands = [e for e in evte if e > h]
        if not cands:
            continue
        e = cands[0]
        parts = []
        pp = h + 273
        while pp + 6 < e:
            code = fw(pp)
            if code <= 0.0:
                break
            px=fw(pp+1); py=fw(pp+2); pz=fw(pp+3)
            parts.append((int(code/1000), px, py, pz))
            pp += 7
        showers.append(parts)
    return showers

def spectra(fname):
    showers = parse_showers(fname)
    g, ep, mu = [], [], []
    for parts in showers:
        for pid, px, py, pz in parts:
            m = MASS.get(pid, 0.0)
            ptot = (px*px+py*py+pz*pz)**0.5
            ekin = (m*m + ptot*ptot)**0.5 - m
            if pid == 1:
                g.append(ekin)
            elif pid in (2, 3):
                ep.append(ekin)
            elif pid in (5, 6):
                mu.append(ekin)
    return len(showers), np.array(g), np.array(ep), np.array(mu)

if __name__ == '__main__':
    base = os.path.expanduser('~/corsika-78010')
    files = {
        'ef0': base + '/run/figure4_ef0_out/DAT004005',
        'efp': base + '/run/figure4_efp_out/DAT004006',
        'efm': base + '/run/figure4_efm_out/DAT004007',
    }
    out = {}
    for key, f in files.items():
        n, g, e, m = spectra(f)
        print(key, f, 'showers=', n, 'g=', len(g), 'e=', len(e), 'mu=', len(m), flush=True)
        out[key+'_g'] = g; out[key+'_e'] = e; out[key+'_m'] = m
        out[key+'_n'] = np.array([n])
    np.savez_compressed('/tmp/opencode/fig4_spectra.npz', **out)
    print('saved /tmp/opencode/fig4_spectra.npz')
