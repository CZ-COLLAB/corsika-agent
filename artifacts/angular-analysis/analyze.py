#!/usr/bin/env python3
"""CORSIKA DAT reader + muon analyser for the zenith-angle flux reproduction
of Cohu et al. (arXiv:2112.06606) Figure 2, using SIBYLL 2.3e + UrQMD.

Reads Fortran unformatted CORSIKA particle files, extracts mu+/- at the
observation level, and returns per-shower yields.

DAT layout (default block 22932 B = 5733 words, sub-block 273 words):
  each sub-block starts with a 4-char marker: RUNH/EVTH/DATA/EVTE/RUNE/LONG
  EVTH  : event header, starts a new shower, particle DATA sub-blocks follow
  DATA  : 7 words per particle (8 with THIN weight)
"""
import struct
import numpy as np
from collections import defaultdict

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


def parse_events(fname, nwords=7):
    block = read_blocks(fname)
    nw = len(block) // 4
    F4 = struct.Struct('<f')
    I4 = struct.Struct('<i')

    def fw(w):
        return F4.unpack_from(block, w * 4)[0]

    def iw(w):
        return I4.unpack_from(block, w * 4)[0]

    def mk(w):
        return block[w * 4:w * 4 + 4]

    marks = {}
    for i in range(nw):
        if i % 273 == 0:
            m = mk(i)
            if m in (b'EVTH', b'EVTE', b'RUNH', b'RUNE'):
                marks[i] = m
    evth = sorted(i for i, m in marks.items() if m == b'EVTH')
    evte = sorted(i for i, m in marks.items() if m == b'EVTE')

    events = []
    for h in evth:
        cands = [e for e in evte if e > h]
        if not cands:
            continue
        e = cands[0]
        prim = iw(h + 2)
        eprim = fw(h + 3)
        theta = fw(h + 10)
        parts = []
        pp = h + 273
        while pp + nwords - 1 < e:
            code = fw(pp)
            if code <= 0.0:
                break
            px = fw(pp + 1)
            py = fw(pp + 2)
            pz = fw(pp + 3)
            x = fw(pp + 4)
            y = fw(pp + 5)
            t = fw(pp + 6)
            parts.append((code, px, py, pz, x, y, t))
            pp += nwords
        events.append(dict(prim=prim, eprim=eprim, theta=theta, parts=parts))
    return events


def muons(fname):
    """Return arrays of muon kinematics for all showers in the file."""
    ev = parse_events(fname)
    pid = []
    px = []
    py = []
    pz = []
    x = []
    y = []
    per_shower = []
    for e in ev:
        n = 0
        for code, ppx, ppy, ppz, xx, yy, tt in e['parts']:
            p = int(code / 1000)
            if p in (5, 6):
                pid.append(p)
                px.append(ppx)
                py.append(ppy)
                pz.append(ppz)
                x.append(xx)
                y.append(yy)
                n += 1
        per_shower.append((e['prim'], e['eprim'], n))
    return dict(
        nshower=len(ev),
        pid=np.array(pid, dtype=int),
        px=np.array(px), py=np.array(py), pz=np.array(pz),
        x=np.array(x), y=np.array(y),
        per_shower=per_shower,
    )


if __name__ == '__main__':
    import sys
    r = muons(sys.argv[1])
    print(f"showers={r['nshower']}  muons={len(r['pid'])}")
    for prim, eprim, n in r['per_shower']:
        print(f"  prim={prim} E={eprim:.3g} GeV  n_mu={n}")
    if len(r['pid']):
        pt = np.sqrt(r['px'] ** 2 + r['py'] ** 2 + r['pz'] ** 2)
        th = np.degrees(np.arccos(np.clip(r['pz'] / pt, -1, 1)))
        ek = np.sqrt(MASS[5] ** 2 + pt ** 2) - MASS[5]
        print(f"  Ekin(GeV): min={ek.min():.3f} med={np.median(ek):.3f} max={ek.max():.3f}")
        print(f"  theta_mu(deg): min={th.min():.2f} med={np.median(th):.2f} max={th.max():.2f}")
        print(f"  r(m): med={np.median(np.hypot(r['x'], r['y']))/100:.2f}")
