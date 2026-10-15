# Build evidence and interaction-model versions

Executables (CORSIKA 7.8010) used for the reported results:

| Executable | Used for | Version verified from the binary |
| --- | --- | --- |
| `corsika78010Linux_SIBYLL_urqmd` | SIBYLL production and angular scan | `SIBYLL 2.3e` (`strings` evidence: `SIBYLL 2.3e`, `sibyll2.3e`) |
| `corsika78010Linux_QGSIII_urqmd` | QGSJET production | `QGSJET-III` (`strings` evidence: `QGSJET-III`, `qgsjet-III`; data files `qgsdat-III`, `sectnu-III`) |

Low-energy interaction model: **UrQMD 1.3.1**
(`strings` evidence: `UrQMD 1.3.1`, `UrQMD: Version 1.3b (10035/10002)`;
cross-section data file `UrQMD-1.3.1-xs.dat`).

Build configuration (`include/config.h`, `run/Makefile`):

- high-energy model `CORHEMODEL=SIBYLL`, low-energy model `CORLEMODEL=URQMD`;
- `-DNO_EXTERNAL_ATMOSPHERES` (standard atmosphere models only);
- `__CURVED__` and `__EFIELD__` compiled in for the SIBYLL build used for
  the angular scan; the electric field is set to zero in the steering cards
  (`ez = 0`, i.e. no field applied);
- the full generated `config.h` is included in this directory.

Common runtime options of the production cards (see `production/cards/`):

```
PRMPAR  14            proton
THETAP  <0 or 75>     fixed direction
PHIP    -180. 180.
ECUTS   0.3 0.3 0.003 0.003
OBSLEV  0.            sea level
MAGNET  20.40 43.23   (production)   /  22.71 40.96  (angular scan)
SIBYLL  T 0 / QGSJET T 0
SIBSIG  T   / QGSSIG  T
ELMFLG  T T
```

The angular scan additionally used `ESLOPE -1.7` over 10–10^6 GeV with
reweighting to the Papini spectrum (importance sampling).
