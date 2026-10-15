#!/usr/bin/env python3
"""Parse the 50000-shower Figure-4 DAT files into kinetic-energy arrays.

Output: run/fig4_spectra_50k.npz with keys ef0_g/e/m, efp_*, efm_* and
ef0_n/efp_n/efm_n (number of showers), same convention as the 20k npz.
"""
import os
import struct
import numpy as np

MASS = {1: 0.0, 2: 0.000511, 3: 0.000511, 5: 0.105658, 6: 0.105658,
        13: 0.13957, 14: 0.13957}


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
    F4 = struct.Struct('<f')

    def fw(w):
        return F4.unpack_from(block, w * 4)[0]

    def mk(w):
        return block[w * 4:w * 4 + 4]

    evth = [i for i in range(0, nw, 273) if mk(i) == b'EVTH']
    evte = [i for i in range(0, nw, 273) if mk(i) == b'EVTE']
    showers = []
    ei = 0
    for h in evth:
        while ei < len(evte) and evte[ei] < h:
            ei += 1
        if ei == len(evte):
            break
        e = evte[ei]
        parts = []
        pp = h + 273
        while pp + 6 < e:
            code = fw(pp)
            if code <= 0.0:
                break
            parts.append((int(code / 1000), fw(pp + 1), fw(pp + 2), fw(pp + 3)))
            pp += 7
        showers.append(parts)
    return showers


def spectra(fname):
    showers = parse_showers(fname)
    g, ep, mu = [], [], []
    for parts in showers:
        for pid, px, py, pz in parts:
            m = MASS.get(pid, 0.0)
            ptot = (px * px + py * py + pz * pz) ** 0.5
            ekin = (m * m + ptot * ptot) ** 0.5 - m
            if pid == 1:
                g.append(ekin)
            elif pid in (2, 3):
                ep.append(ekin)
            elif pid in (5, 6):
                mu.append(ekin)
    return len(showers), np.array(g), np.array(ep), np.array(mu)


if __name__ == '__main__':
    base = os.path.expanduser('~/corsika-78010/run')
    files = {
        'ef0': base + '/figure4_ef0_50k_out/DAT004008',
        'efp': base + '/figure4_efp_50k_out/DAT004009',
        'efm': base + '/figure4_efm_50k_out/DAT004010',
    }
    out = {}
    for key, f in files.items():
        n, g, e, m = spectra(f)
        print(key, f, 'showers=', n, 'g=', len(g), 'e=', len(e),
              'mu=', len(m), flush=True)
        out[key + '_g'] = g
        out[key + '_e'] = e
        out[key + '_m'] = m
        out[key + '_n'] = np.array([n])
    np.savez_compressed(base + '/fig4_spectra_50k.npz', **out)
    print('saved', base + '/fig4_spectra_50k.npz')
