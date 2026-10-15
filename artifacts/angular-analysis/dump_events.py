#!/usr/bin/env python3
"""Print per-event 'Eprim n_mu' for a CORSIKA DAT file (mu+/- at obs level)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze import parse_events


def main():
    for f in sys.argv[1:]:
        for e in parse_events(f):
            n = sum(1 for p in e['parts'] if int(p[0] / 1000) in (5, 6))
            print(f"{e['eprim']:.6g} {n}")


if __name__ == '__main__':
    main()
