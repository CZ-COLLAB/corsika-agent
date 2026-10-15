#!/usr/bin/env python3
"""Parse CORSIKA binary particle output (DATnnnnnn) and build
energy distributions of gamma, electron/positron, and muon+/- at the
observation level, matching paper Figure 4 (no-electric-field baseline).

Usage:
    python3 parse_fig4.py DATfile
"""
import struct
import sys
import numpy as np

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
            tr = f.read(4)
            chunks.append(blk)
    return b''.join(chunks)

def parse(fname):
    block = read_blocks(fname)
    nw = len(block) // 4
    F4 = struct.Struct('<f')
    I4 = struct.Struct('<i')
    def fword(w): return F4.unpack_from(block, w*4)[0]
    def iword(w): return I4.unpack_from(block, w*4)[0]
    def mark_at(w): return block[w*4:w*4+4]
    evth = sorted([i for i in range(nw) if i % 273 == 0 and mark_at(i) == b'EVTH'])
    evte = sorted([i for i in range(nw) if i % 273 == 0 and mark_at(i) == b'EVTE'])
    events = []
    for h in evth:
        # find matching EVTE = first EVTE after this EVTH
        cands = [e for e in evte if e > h]
        e = cands[0] if cands else nw
        if e == nw:
            continue
        ev_num = iword(h+1)
        prim   = iword(h+2)
        eprim  = fword(h+3)
        parts = []
        pp = h + 273  # particle data starts after 273-word EVTH
        while pp + 6 < e:
            code = fword(pp)
            if code <= 0.0:
                break
            px = fword(pp+1); py = fword(pp+2); pz = fword(pp+3)
            x  = fword(pp+4); y  = fword(pp+5); t  = fword(pp+6)
            pid = int(code / 1000)
            parts.append((pid, code, px, py, pz, x, y, t))
            pp += 7
        events.append(dict(num=ev_num, prim=prim, eprim=eprim, parts=parts))
    return events

def collect(events):
    """Return dict of pid -> array of kinetic energies (GeV)."""
    from collections import defaultdict
    out = defaultdict(list)
    for ev in events:
        for pid, code, px, py, pz, x, y, t in ev['parts']:
            # kinetic energy = total - rest mass
            m = {1:0.0, 2:0.000511, 3:0.000511, 5:0.105658, 6:0.105658,
                 13:0.13957, 14:0.13957}.get(pid, 0.0)
            ptot = (px*px+py*py+pz*pz)**0.5
            etot = (m*m + ptot*ptot)**0.5
            Ekin = etot - m
            out[pid].append((Ekin, ptot))
    return out

def main():
    fname = sys.argv[1]
    events = parse(fname)
    n_part = sum(len(ev['parts']) for ev in events)
    print(f"events: {len(events)}  total particles: {n_part}")
    from collections import Counter
    cnt = Counter()
    for ev in events:
        for p in ev['parts']:
            cnt[p[0]] += 1
    print("pid counts:", dict(cnt))
    data = collect(events)
    np.save('/tmp/opencode/fig4_energies.npy', {
        'g': [e for e,_ in data.get(1,[])], 
        'ep': [e for e,_ in data.get(2,[])],
        'em': [e for e,_ in data.get(3,[])],
        'mup': [e for e,_ in data.get(5,[])],
        'mum': [e for e,_ in data.get(6,[])],
    }, allow_pickle=True)
    for k,v in data.items():
        ek = [e for e,_ in v]
        if ek:
            print(f"pid {k}: n={len(ek)} Ekin min={min(ek):.4f} med={np.median(ek):.4f} max={max(ek):.4f}")

if __name__ == '__main__':
    main()
