
# Planetary Migration: CORSIKA 7 on Other Planets

Migrating CORSIKA 7 from Earth to other planets (Mars, Venus, …) for cosmic-ray shower /
surface μ flux simulations. The core capability is **changing the atmosphere + magnetic
field + observation level via runtime steering cards (the ATMOD 0 family), with no
recompilation**, so the same binary runs on different planets.

This skill covers **all** migration-relevant parameters, not just the atmosphere:

| Parameter category | CORSIKA card / source location | Planet relevance |
|--------------------|-------------------------------|------------------|
| Atmosphere (column-depth profile) | `ATMOD 0` + `ATMA/ATMB/ATMC/ATMLAY` | Core |
| Magnetic field | `MAGNET BX BZ` | High (→0 for planets with no field) |
| Gravity g | Used only to convert pressure to column depth (external) | High |
| Radius R | `C(1)`/`cRearth` (CURVED mode only) | Medium (irrelevant for flat atmosphere ≤70°) |
| Composition | `COMPOS`/`AVERAW` (three slots N/O/Ar) | Medium (CO₂ cannot be represented) |
| Observation level | `OBSLEV` | High (surface vs cloud layer) |
| Temperature profile T(h) | Used to construct the atmosphere (external script) | High |
| Primary spectrum | Same spectrum as Earth, modulated by the planet's orbit/field (external) | Medium |


===============================================================================
1. General Migration Approach
===============================================================================

The CORSIKA 7 atmosphere = 4 exponential layers + 1 fixed linear top layer (see the
corsika7 skill's usage-guide 4.7):

    Layer i (1..4):  t(h) = A_i + B_i * exp(-h/C_i)  defined on [H_i, H_{i+1}]
    Layer 5 (linear):  t(h) = A_5 - h/C_5

where t(h) is the slant column depth (g/cm²) at altitude h, and HLAY(6) = A_5 * C_5 = 112.8 km
is the top of the atmosphere. **The layer-5 coefficients A_5=0.01128292 and C_5=1e9 are
hard-coded in the source** (DATAC; ATMA/ATMB/ATMC only read 4 values) and cannot be changed
with cards → the top of the atmosphere for any planet is pinned at 112.8 km (a top-layer tail
with column depth <~0.01 g/cm², irrelevant for μ physics).

Two migration routes:
  (a) change the source defaults (the original Mars approach, requires recompiling);
  (b) runtime `ATMOD 0` + `ATMA/ATMB/ATMC/ATMLAY` cards (**recommended, no recompiling**).

**Dominant factors**: the μ flux is determined by two independent mechanisms—
  (1) energy loss: μ ionization loss ≈ 2 MeV/(g/cm²), crossing column depth X requires
      E_μ ≳ 2 MeV·X; this term depends only on the column depth X above the observation level;
  (2) decay loss: survival probability exp(-L/γcτ), where L is the geometrical distance from
      the production point to the observation level, determined by the density profile ρ(h)
      (X = ∫ρ dh; equal column depth ≠ equal production altitude).
  The column depth is the zeroth-order dominant term and the density profile is a second-order
  correction, especially significant for low-energy μ (where γcτ is comparable to the
  atmosphere's height). When migrating, do not draw quantitative conclusions directly from
  column-depth scaling alone; rely on full CORSIKA MC results.


===============================================================================
2. Mars
===============================================================================

2.1 Authoritative parameters (NSSDCA Mars Fact Sheet, confirmed to exist)

  Surface pressure  6.36 mbar (4.0~8.7 mbar with season)
  Surface density   ~0.016 kg/m³
  Scale height      11.0 km
  Mean temperature  ~214 K
  Mean molecular weight 43.49
  Surface gravity   3.73 m/s²
  Composition (by volume) CO2 95.1%, N2 2.59%, Ar 1.94%, O2 0.16%, CO 0.06%
  Mean radius       3389.5 km
  → Column depth = P/g ≈ 171 kg/m² ≈ 17 g/cm² (about 1.7% of Earth's)

2.2 CORSIKA 5-layer card values (ATMOD 0)

  ATMA    = 0. 0. 0. 0.
  ATMB    = 18.84 16.82 204.9 204.9
  ATMC    = 1.1E6 1.2E6 8.E5 8.E5
  ATMLAY  = 1.5E6 6.0E6 1.0E7 1.1E7   (cm = 15/60/100/110 km)
  Surface column depth = 18.84 g/cm² ✓

2.3 Key pitfall: the 4th ATMLAY value must be ≤ 110 km

  The Mars atmosphere model's original layer boundary H5=120 km would exceed H6=112.8 km,
  causing a "BAD SELECTION OF ATMOSPHERIC PARAMETERS ... THICKL negative" STOP.
  Fix: change the 4th value to 110 km (1.1E7); layers 3/4 share the same exponential
  204.9*exp(-h/8e5) and join seamlessly.
  The banner should print:
    H=0..15:  T=18.84*exp(-H/11)
    H=15..60: T=16.82*exp(-H/12)
    H=60..100: T=204.9*exp(-H/8)
    H=100..110: T=204.9*exp(-H/8)
    H=110..112.8: T=0.01128292-H/1e4

2.4 Other parameters (complete)

  - Magnetic field: Mars has no global dipole field → `MAGNET 0.01 0.01`.
  - Composition: keep N2/O2 (see the CO₂ compromise in section 6).
  - Observation level: `OBSLEV 0` (surface). The atmosphere is thin and the angular
    distribution is concentrated → THETAP 0 suffices.
  - Primary spectrum: Papini solar-minimum proton spectrum `phi_p(E)=3.2009e8*(1000E+920)^-4*(1000E)^1.25`.
  - Hadronic model: SIBYLL 2.3e + UrQMD; ECUTS 0.3 0.3 0.003 0.003.

2.5 Reference values for the Mars surface μ flux

  μ yield is extremely low (thin atmosphere): 10 GeV→0.107/shower, 100 TeV→7.49/shower
  (about 1% of Earth's). But showers are extremely fast (~5 ms), so compensate with a very
  large NSHOW (order 1e5).
  Mars/Earth ratios: 0.3 GeV=1.385, 1 GeV=0.692, 10 GeV=0.252, 100 GeV=0.189
  (Mars is slightly higher at the low-energy end—less μ decay loss in a thin atmosphere;
  five times lower at the high-energy end—insufficient cascade development depth).


===============================================================================
3. Venus
===============================================================================

3.1 Authoritative parameters (NSSDCA Venus Fact Sheet, confirmed to exist)

  Surface pressure  92 bar
  Surface density   ~65 kg/m³
  Scale height      15.9 km
  Mean temperature  737 K
  Mean molecular weight 43.45
  Surface gravity   8.87 m/s²
  Composition (near-surface, by volume) CO2 96.5%, N2 3.5% (+SO2 150ppm, Ar 70ppm)
  Mean radius       6051.8 km
  → Column depth = P/g ≈ 1.037e5 g/cm² (about 100× Earth's); 1 bar level ≈ 49.9 km (1123 g/cm²)

3.2 Temperature profile (VIRA approximation, source Seiff 1985 / NSSDCA; must be cross-checked against the original table before publication)

  Piecewise-linear nodes h(km)→T(K):
    0:735  5:695  10:655  15:615  20:575  25:535  30:495  35:455  40:415
    45:375  50:350  55:310  60:260  65:245  70:230  75:215  80:200  85:190
    90:180  95:175  100:170  110:175  120:250

3.3 CORSIKA 5-layer card values (ATMOD 0)

  Layer boundaries H=[0,20,40,50,100,112.8] km; **set the observation level (50 km cloud layer)
  as a boundary node** to guarantee an exact column depth there.

  ATMA    = -10063.847 -1886.811 -325.75 -0.073209877
  ATMB    = 113784.25 127644.89 275874.86 16495556
  ATMC    = 1699411 1284287.7 950688.26 520409.03
  ATMLAY  = 2.E6 4.E6 5.E6 1.E7   (cm = 20/40/50/100 km)
  Validation: t(0)=1.0372e5; t(50 km)=1108 g/cm² (observation level)

3.4 Other parameters (complete)

  - Magnetic field: Venus has no intrinsic magnetic field → `MAGNET 0.01 0.01`.
  - Observation level: surface `OBSLEV 0` (column depth 1.037e5; μ are almost fully absorbed,
    ~1.2 μ/event, lateral r<~700 m); cloud layer `OBSLEV 5.0E6 cm` (50 km, column depth
    1108 ≈ Earth sea level, ~520 μ/event, physically meaningful). → What corresponds to
    Earth sea level is the **Venus surface**.


===============================================================================
4. General Workflow (new-planet checklist, covering all parameters)
===============================================================================

  1. Consult the NSSDCA Planetary Fact Sheet for **surface pressure P, gravity g, scale height,
     mean molecular weight, temperature T(h), composition, radius R**. Column depth
     t(0)=P/g (Pa/(m/s²)=kg/m², ×0.1=g/cm²).
  2. Construct the temperature profile T(h) (authoritative reference atmospheres: Venus VIRA,
     Mars NASA Glenn model; for other planets find the corresponding reference atmosphere
     and cite the source).
  3. Integrate the hydrostatic + ideal-gas equations to get the column-depth profile t(h):
         d lnP/dh = -Mmol·g/(R·T), t(h)=P(h)/g × 0.1
  4. Choose layer boundaries H (set the target observation level as a boundary node), fit 4
     exponential layers t=A+B·exp(-h/C); layer 5 is the hard-coded linear term
     A5=0.01128292/C5=1e9, with H6=112.8 km automatic.
     Constraint: each layer's column depth THICKL(L)≥0 and ≥AATM(L-1) (monotonic).
  5. Write the steering card: ATMOD 0 + ATMA/ATMB/ATMC/ATMLAY + target OBSLEV +
     MAGNET (for planets with a field, look up its strength; otherwise 0.01 0.01) +
     ECUTS/PRMPAR/THETAP/primary spectrum.
  6. First run a 1-shower smoke test to verify the 5-layer parameters printed in the banner
     and the surface column depth.
  7. Production + analysis (read the binary DAT, or convert to ROOT with CorsikaPlottermini;
     Papini spectrum weighting).


===============================================================================
5. Authoritative Source List (all confirmed online, 2026-09)
===============================================================================

  [1] NASA NSSDCA Mars Fact Sheet
      https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html
      Last Updated: 19 May 2025 (surface pressure/density/scale height/temperature/molecular weight/gravity/composition)
  [2] NASA NSSDCA Venus Fact Sheet
      https://nssdc.gsfc.nasa.gov/planetary/factsheet/venusfact.html
      Last Updated: 11 January 2024 (same as above)
  [3] NASA Glenn, Mars Atmosphere Model (metric)
      https://www.grc.nasa.gov/www/k-12/airplane/atmosmrm.html
      Last Updated: May 13 2021 (Mars two-segment pressure/temperature formulas, MGS 1996 data)
  [4] Seiff, A. et al. 1985, Adv. Space Res. 5(11), 3-58 (VIRA; original table not verified
      online, must be cross-checked before use)
  [5] Globus, Fedynitch & Blandford 2021, ApJ 909, 107, arXiv:2101.00530
      (uses the VeGa-2 profile for Venus; a segmented MGS pressure formula for Mars)
  [6] Ulrich, R. et al. 2021, "Hadron cascades in CORSIKA 8", ICRC 2021
      (CORSIKA 8 benchmark for the Mars atmosphere)


===============================================================================
6. Physics Approximations and Known Limitations (all parameters)
===============================================================================

  * CO₂ composition cannot be represented: CORSIKA 7's COMPOS(3) only has N2/O2/Ar, with no
    carbon slot. For Mars (95% CO₂)/Venus (96.5% CO₂) only N2/O2 can be kept. The impact on
    the μ flux is negligible (μ come mainly from π→μ, and the medium's atomic number is a
    small second-order effect), but papers must state this explicitly (the same compromise
    as ICRC 2021).
  * Hadronic-model target-nucleus calibration: SIBYLL/EPOS/QGSJET/UrQMD are calibrated for
    air with TAR≈14.6. Solid media (lunar regolith <A>≈21) need separate calibration—the
    atmospheric migration in this skill is unaffected, but solid surfaces require care.
  * Layer-5 top H6=112.8 km hard-coded: the top of the atmosphere is pinned at 112.8 km;
    card values where the original planet's atmosphere top is higher must be truncated to ≤110 km.
  * Magnetic field: CORSIKA only approximates it with a constant MAGNET BX BZ; set 0.01 0.01
    for planets with no intrinsic field.
  * Gravity/radius: for a flat atmosphere at ≤70° the planetary radius is irrelevant; g is
    used only for column-depth conversion. Only CURVED mode requires changing C(1)/cRearth
    (radius 6371→3389 km).
  * Zenith angles >70° require a CURVED build; for a flat atmosphere at ≤70° the planetary
    radius is irrelevant.
