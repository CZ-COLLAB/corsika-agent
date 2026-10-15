================================================================================
  CORSIKA 7.8010 Usage Guide
  Compiled from CORSIKA_GUIDE7.8010.pdf (207 pages, 2025-04-03) + README
================================================================================

Table of contents:
  1. Overview
  2. Installation and Compilation
  3. Important Compile Options
  4. Steering Cards in Detail
     4.1 Run Identification and Random Numbers
     4.2 Primary Particle and Energy
     4.3 Angle Definitions
     4.4 Observation Level and Energy Cuts
     4.5 Hadronic Interaction Models
     4.6 Electromagnetic Interactions
     4.7 Atmosphere Models
     4.8 Geomagnetic Field
     4.9 Output Control
     4.10 Thinning (THIN)
     4.11 Other Common Cards
  5. CURVED Mode
  6. Running Methods and Examples
  7. DAT Binary Output Format
     7.1 Block Structure
     7.2 Particle Data Sub-block (7 words/particle)
     7.3 Key Event-Header Sub-block Fields
  8. Particle Code Table
  9. Coordinate Systems
  10. Utilities
  11. Common Issues and Recommendations


================================================================================
1. Overview
================================================================================

CORSIKA (COsmic Ray SImulations for KAscade) is a detailed extensive air shower
(EAS) simulation program developed at KIT (Karlsruhe Institute of Technology),
Germany. It simulates the cascade processes triggered when high-energy cosmic-ray
particles enter the atmosphere, and records the various secondary particles (γ, e±,
μ±, hadrons, neutrinos, etc.) reaching the observation level. Widely used in:

  - Large ground-based experiments: Auger, IceCube/IceTop, KASCADE, HAWC, LHAASO, etc.
  - Atmospheric Cherenkov telescopes: H.E.S.S., MAGIC, VERITAS, CTA
  - Neutrino astronomy: studies of the atmospheric neutrino background

Energy range: ~10^11 eV to ~10^20 eV
Current version: 7.8010 (2025-04-03)


================================================================================
2. Installation and Compilation
================================================================================

2.1 Obtaining the source code

From the KIT server (password required):
  https://web.iap.kit.edu/corsika/download/
  Username: corsika
  Go to corsika-v780/ → corsika-78010.tar.gz

2.2 Installation steps

  tar xzf corsika-78010.tar.gz
  cd corsika-78010
  ./coconut                          # no arguments, interactive installation

  # or pipe preset options (non-interactive):
  # echo "corsika-78010/install_script.inp" | ./coconut

2.3 coconut interactive walkthrough

coconut asks for the following in sequence:
  a) Operating system type (Linux, MacOS, etc.)
  b) Fortran compiler (gfortran, ifort, etc.)
  c) Whether MPI parallelism is needed (PARALLEL)
  d) Whether to enter expert mode — YES is recommended, allows custom compile options
  e) Choice of program options to enable (see Section 3)
  f) Choice of hadronic interaction model

In expert mode each feature can be switched on/off individually. After compilation,
the executable corsika and the utility programs are located in the run/ directory.

2.4 Base data files

The run/ directory must contain the following data files (automatically downloaded
or copied during compilation):
  - NUCNUCCS                   nucleus-nucleus/nucleon-nucleus cross-section data
  - EGSDAT6_x.x                electromagnetic interaction data (EGS4)
  - Cross-section data for the hadronic models: qgsdat-II-04, sectnu-II-04, etc.
  - VENUSDAT (VENUS model)
  - UrQMD-*-xs.dat (UrQMD model)


================================================================================
3. Important Compile Options
================================================================================

The following options must be selected during coconut installation (expert mode):

| Option        | Description                                                       |
|---------------|-------------------------------------------------------------------|
| CURVED        | curved-atmosphere version, supports large zenith angles (>70°) up to nearly 90° |
| THIN          | statistical thinning, reduces the particle output for high-energy events |
| THINMAX       | enhanced version of THIN, all thinned particles kept at maximum weight |
| MULTITHIN     | multi-thinning, supports up to 6 independent thinning parameter sets |
| CERENKOV      | Cherenkov photon simulation                                       |
| IACT          | imaging atmospheric Cherenkov telescopes (MAGIC, HESS, CTA)       |
| ATMEXT        | external atmosphere models (MODTRAN, GDAS)                        |
| SLANT         | longitudinal profiles in slant depth                              |
| UPWARD        | upward-going particles (neutrinos, τ leptons)                     |
| EHISTORY      | adds parent/grandparent history information to the output         |
| MUPROD        | tracks detailed muon production information                       |
| ROOTOUT       | direct ROOT format output (COAST post-processing conversion recommended) |
| COMPACT       | compact particle output format                                    |
| INCLINED      | inclined observation plane                                        |
| NUPRIM        | primary neutrino mode                                             |
| CHARM/TAULEP  | charmed-particle/τ-lepton production and decay                    |
| PRESHOWER     | preshower for ultra-high-energy γ                                 |
| CONEX         | fast cascade-equation simulation (hybridized with full CORSIKA)   |
| PARALLEL      | MPI parallelization                                               |
| COASTUSERLIB  | COAST user library interface                                      |
| COREAS        | radio-emission simulation                                         |

Note: CURVED and CONEX cannot be enabled at the same time (CONEX internally uses part of the CURVED code).


================================================================================
4. Steering Cards in Detail
================================================================================

Steering card format:
  KEYWRD  arg1  arg2  ...  [comment]
  Keyword is left-aligned (≤6 characters), parameters separated by spaces, at most 512 columns.
  Comment lines: first character is c/C followed by a space, or *.
  Case-insensitive (except for character-type parameters such as EPOPAR/DATDIR/DIRECT).

================================================================================
4.1 Run Identification and Random Numbers
================================================================================

RUNNR   NRRUN             Format (A5, I)  Default 1
  Run number, used to generate output file names (DATnnnnnn).
  Range: 0 ≤ NRRUN ≤ 999999 (NRREXT option: 0~999999999)

EVTNR   SHOWNO            Format (A5, I)  Default 1
  Starting event number; subsequent events are incremented automatically.

SEED    ISEED1 ISEED2 ISEED3  Format (A4, 3I)
  Random-number seed sequences k (assigned in order of appearance):
    k=1: hadronic shower
    k=2: EGS4 electromagnetic part
    k=3: Cherenkov photons
    k=4: IACT/AUGERHIT offset
  At least the two seeds k=1,2 are required. Modifying ISEED1 alone yields a different sequence.
  ISEED2/3 are used to skip a large number of random-number calls; this consumes a lot of CPU and is not recommended.
  Limit: 1 ≤ ISEED1 ≤ 900,000,000

  # Typical example:
  SEED 12345 0 0
  SEED 67890 0 0

================================================================================
4.2 Primary Particle and Energy
================================================================================

NSHOW   NSHOW             Format (A5, I)  Default 10
  Number of events generated per run. NSHOW ≥ 1

PRMPAR  ID                Format (A6, I)  Default 14
  Primary particle type code:
    1   = γ (photon)
    2   = e⁺
    3   = e⁻
    5   = μ⁺
    6   = μ⁻
    14  = proton (p)
    5626 = iron nucleus (⁵⁶Fe²⁶)
    4026 = calcium nucleus
    1608 = oxygen nucleus
    1206 = carbon nucleus
  See the particle code table in Section 8.

ERANGE  LLIMIT  ULIMIT    Format (A6, 2F)  Default 1.E4, 1.E4
  Primary particle total energy range (GeV, including rest mass).
  If LLIMIT = ULIMIT, the energy is fixed.
  Recommended upper limits: HDPM 1E8, VENUS 2E7, DPMJET 1E10.

ESLOPE  PSLOPE            Format (A6, F)  Default 0.
  Energy spectrum index γ, spectral shape dN/dE ∝ E^γ.
  Has no effect when the energy is fixed.

================================================================================
4.3 Angle Definitions
================================================================================

THETAP  THMIN  THMAX      Format (A6, 2F)  Default 0., 0.
  Primary particle zenith-angle range (degrees). Within the range, angles are drawn
  from a sinθ·cosθ distribution (the detection rate of a horizontal detector under a
  uniform isotropic flux).
  Standard mode limit: THETPR(i) ≤ 70°
  CURVED mode limit: THETPR(i) < 90°
  If THMIN = THMAX, the angle is fixed.

PHIP    PHMIN  PHMAX      Format (A4, 2F)  Default 0., 0.
  Azimuth-angle range (degrees). ϕ=0° points to magnetic north, ϕ=90° points to west.
  Range: -360° ≤ PHIPR(i) ≤ 360°

================================================================================
4.4 Observation Level and Energy Cuts
================================================================================

OBSLEV  HEIGHT            Format (A6, F)  Default 110.E2 (cm, i.e. 110 m a.s.l.)
  Observation height (cm a.s.l.). Up to 10 observation levels (each call defines one).
  Only 1 observation level in CURVED mode.
  Sea level is set to 0.

ECUTS   EHAD  EMU  EELEC  EGAM  Format (A5, 4F)  Default 0.3, 0.3, 0.003, 0.003
  Particle kinetic-energy cuts (GeV); particles below these values are discarded:
    EHAD: hadrons (except π⁰), nucleons counted per nucleon
    EMU:  μ⁺/μ⁻
    EELEC: e⁺/e⁻ (also the NKG calculation threshold, recommended < 0.08 GeV)
    EGAM: photons
  Limits: EHAD≥0.05, EMU≥0.01, EELEC/EGAM≥0.00005

================================================================================
4.5 Hadronic Interaction Models
================================================================================

High-energy models (choose one main model, set the others to F):

  SIBYLL  F  DEBUGLEV     Format (A6, L, I)  Default T, 0
    Enables the SIBYLL 2.3d/e model, default T. DEBUGLEV: debug level.

  SIBSIG  F               Format (A6, L)    Default T
    Use SIBYLL cross sections.

  QGSJET  F  DEBUGLEV     Format (A6, L, I)  Default T, 0
    QGSJET-II-04 or QGSJET01d (depending on compile options).

  EPOS    F  DEBUGLEV     Format (A5, L, I)  Default T, 0
    EPOS LHC model.

  DPMJET  F  DEBUGLEV     Format (A6, L, I)  Default T, 0
    DPMJETIII model.

  FLUKA   F               Format (A5, L)    Default T
    Low-energy hadronic model (requires the FLUKA interface selected at compile time).

  GHEISHA F               Format (A7, L)    Default T
    Built-in low-energy hadronic model (GHEISHA 2002).

  Note: Switching between the high-energy models is not mutually exclusive, but in
        practice only one of them is ever used.
        The high-energy/low-energy transition energy is set by the HILOW card
        (default 80 GeV).

================================================================================
4.6 Electromagnetic Interactions
================================================================================

ELMFLG  FNKG  FEGS        Format (A6, 2L)  Default T, T
  FNKG: use the NKG analytic formula to treat electromagnetic sub-showers
       (automatically disabled in CURVED mode, since curvature invalidates the formula)
  FEGS: use EGS4 to accurately simulate the electromagnetic cascade of e⁺/e⁻/γ
  # normally both are set to T (both sides treated simultaneously)
  # if only the muon flux is of interest, set FNKG=F, FEGS=T to speed up the simulation

================================================================================
4.7 Atmosphere Models
================================================================================

ATMOD   MODATM             Format (A5, I)  Default 1
  Atmosphere model number:
    0  = user-defined (requires setting ATMA/ATMB/ATMC/ATMLAY as well)
    1  = US standard atmosphere (Linsley parameterization) [default]
    2~8 = Central European monthly atmospheres (Ulrich)
    11~16 = South Pole atmospheres (MSIS-90-E, Lipari)
    17 = US standard atmosphere (Keilhauer parameterization)
    18~29 = Argentine Malargüe monthly atmospheres (Auger experiment)
    30~41 = South Pole IceTop monthly atmospheres (de Ridder)

ATMA    A1 A2 A3 A4 [A5]   Format (A4, 4F or 5F)
ATMB    B1 B2 B3 B4         Format (A4, 4F)
ATMC    C1 C2 C3 C4 [C5]   Format (A4, 4F or 5F)
  Atmosphere parameters, only used for ATMOD=0 or 10.
  Formula: t(h) = A_i + B_i * exp(-h/C_i)  (layers 1-4)
           t(h) = A_5 - h/C_5               (layer 5, linear approximation)

ATMLAY  H2 H3 H4 H5        Format (A6, 4F)  Default 4.E5, 10.E5, 40.E5, 100.E5 (cm)
  Layer boundary heights, only used for ATMOD=0 or 10.

ATMOSPHERE  IATMO  FREFR  Format (A10, I, L)  Default 0, F
  Use an external MODTRAN atmosphere (requires the ATMEXT compile option).
  IATMO=1~6: tropical/mid-latitude summer/winter/subarctic summer/winter/US standard
  FREFR: whether to account for atmospheric refraction (Cherenkov photons)

ATMFILE  FILENAME         Format (A7, A1024)
  Read an atmosphere profile from a GDAS database fit file, generated with the gdastool utility.

================================================================================
4.8 Geomagnetic Field
================================================================================

MAGNET  BX  BZ             Format (A6, 2F)  Default 20.40, 43.23 (μT, Karlsruhe)
  BX: horizontal component (pointing north, μT)
  BZ: vertical component (pointing down, μT)
  Can be obtained online with the Geomag program:  https://www.ngdc.noaa.gov/geomag/calculators/

================================================================================
4.9 Output Control
================================================================================

DIRECT  PATH              Format (A6, A239)
  Output directory path. Lowercase letters are not automatically uppercased.
  PATH must not start with ~. Current directory: DIRECT ./

PAROUT  FPAROUT  FTABOUT   Format (A6, 2L)  Default T, F
  FPAROUT: whether to write the particle output file (DATnnnnnn)
  FTABOUT: whether to write the table output (DATnnnnnn.tab)

DATBAS  F                 Format (A6, L)    Default F
  Whether to write the DATnnnnnn.dbase database summary file.

LONGI   FLONG  STEPS  FTABLE  FOUT  Format (A5, L, F, L, L)
  Longitudinal-development output control.
  STEPS: output once every STEPS g/cm².

FLONGOUT  F               Format (A8, L)    Default F
  Write longitudinal information into the LONG block of the DAT particle output file.

MAXPRT  N                 Format (A6, I)    Default 1
  Print a detailed log for the first N events; only a summary afterwards.

================================================================================
4.10 Thinning (THIN)
================================================================================

THIN    EFRCTHN  WMAX  RMAX  Format (A4, 3F)  Default 1.E-4, 1.E30, 0.E0
  EFRCTHN: energy-fraction threshold (relative to the primary energy); particles
           below this value are thinned
  WMAX:    maximum weight. Particles whose weight exceeds this are no longer thinned
  RMAX:    radial thinning radius (cm); 0 disables radial thinning
           (particles with r < RMAX are kept with probability (r/RMAX)^4)
  Typical setting: THIN 1.E-6 1.E3 0.

THINH   THINRAT  WEITRAT    Format (A5, 2F)  Default 1., 1.
  Hadronic thinning parameter overrides:
  THINRAT: ε_em/ε_had (electromagnetic/hadronic energy-fraction ratio)
  WEITRAT: WMAX_em/WMAX_had

THINEM  THINRAT  WEITRAT    Format (A6, 2F)  Default 1., 1.
  Electromagnetic thinning parameter overrides (mutually exclusive with THINH).

Thinning efficiency reference (10^15 eV, QGSJET):
  EFRCTHN  time (min)  particle count
  no thinning  98        413078
  1E-6      51        58313
  1E-5      7.2       11466
  1E-4      1.2       2211
  1E-3      0.16      419

================================================================================
4.11 Other Common Cards
================================================================================

FIXCHI  THICK0            Format (A6, F)    Default 0.
  Starting atmospheric depth (g/cm²). The primary particle starts at this vertical depth.
  Mutually exclusive with FIXHEI.

FIXHEI  HEIGHT  N1STTR    Format (A6, F, I)  Default 0., 0
  Fixed first-interaction height (cm). N1STTR=1/2/3 specifies the target nucleus type.

HADFLG  NFLAIN NFLDIF NFLPI0 NFLPIF NFLCHE NFRAGM  Format (A6, 6I)
  Hadronic interaction parameters:
  NFRAGM=2 [default]: cascade fragmentation (experimental pT)
  NFRAGM=0: complete fragmentation into free nucleons
  NFRAGM>2: different fragmentation models

STEPFC  F                 Format (A6, F)    Default 1.
  EGS4 electromagnetic step-length scaling factor.

RADNKG  R                 Format (A6, F)    Default 200.E2 (cm)
  Maximum radius of the NKG lateral distribution.

MUMULT  F                 Format (A6, L)    Default T
  Muon multiple scattering (Molière or Gauss).

MUADDI  F                 Format (A6, L)    Default F
  Muon additional information (parent-particle information) output.

ARRANG  ANGLE             Format (A6, F)    Default 0.
  Angle between the detector-array x axis and magnetic north (degrees).

ECTMAP  E                 Format (A6, F)    Default 1.E2 (GeV)
  Energy threshold for printout — only affects the .lst output, not the particle output.

CURVOUT F                 Format (A7, L)    Default T (CURVED mode)
  In CURVED mode the observation plane follows the Earth's curvature. If F, a planar approximation is used.

EXIT                      Format (A4)
  Must be the last card, marking the end of input.

================================================================================
5. CURVED Mode
================================================================================

5.1 When to Use It

  CURVED mode must be used for zenith angles >70° (in standard mode THETAP is limited to ≤70°).
  CURVED mode treats the Earth as a sphere of radius 6371.315 km and adopts a "sliding
  plane" approximation, discretizing the particle trajectories into a series of steps in
  local Cartesian systems, rotating the coordinate system after each step so that the
  z axis points back toward the Earth's center.

5.2 Main Differences from Standard Mode

  - THETAP upper limit extended from 70° to <90° (up to 180° when combined with UPWARD)
  - NKG formula automatically disabled (since spherical geometry does not apply)
  - only 1 observation level supported
  - output coordinates are lateral distances in the detector system (see Section 9)
  - lateral coordinates are corrected by CORRXY (spherical-projection correction)

5.3 CURVOUT Card

  CURVOUT F (default T):
    T: the observation plane is spherical (follows the Earth's curvature); the output
       coordinates (X', Y') can be used to back-compute the true (X, Y, Z) via
       spherical geometry
    F: the observation plane is a planar approximation, tracking only down to the
       height Z=OBSLEV(1)
    Forced to T between 85° and 95°.

================================================================================
6. Running Methods and Examples
================================================================================

6.1 Run Command

  ./corsika < input_file  [> output.lst]
  # input_file is a text-format steering card file

  Example:
  ./corsika < all-inputs-SIBYLL3 >& DAT000042.lst

6.2 Minimal Input File Example

  ----------------------------------------------------------------
  RUNNR   42          ! run number
  EVTNR   1           ! starting event number
  SEED    12345 0 0   ! hadronic shower seed
  SEED    67890 0 0   ! EGS4 seed
  NSHOW   10000       ! number of events
  PRMPAR  14          ! proton
  ERANGE  1.  1.E5    ! fixed energy (1 TeV)
  THETAP  0.  89.     ! zenith angle 0°~89°
  PHIP    -180. 180.  ! full azimuth range
  SIBYLL  T  0        ! SIBYLL 2.3e model
  SIBSIG  T           ! SIBYLL cross sections
  ELMFLG  T  T        ! NKG + EGS4
  ECUTS   0.3  0.3  0.003  0.003  ! energy cuts
  OBSLEV  0.          ! observation at sea level
  DIRECT  ./          ! output to current directory
  EXIT                ! end
  ----------------------------------------------------------------

6.3 THIN Example

  ----------------------------------------------------------------
  THIN    1.E-6  1.E3  0.    ! thin at 1E-6 of the primary energy, maximum weight 1000
  THINH   1.     100.        ! hadronic weight ratio 100 (muons kept exact)
  ----------------------------------------------------------------

================================================================================
7. DAT Binary Output Format
================================================================================

7.1 Block Structure

DAT files are Fortran sequential unformatted binary, with default block length 22932 bytes
(= 5733 words × 4 bytes; each large block = 21 sub-blocks × 273 words).

                    repeats for each event →
  ┌─────────┬──────────┬────┬──────┬────┬──────┬──────────┐
  │ RUNH    │ EVTH  #1 │DATA│ DATA │... │ EVTE │ EVTH  #2 │...
  │ (runhdr)│ (evthdr) │    │      │    │ (end)│ (evthdr) │
  └─────────┴──────────┴────┴──────┴────┴──────┴──────────┘

  End of file:
  RUNE (run end)

  Each sub-block starts with a 4-character identifier: 'RUNH', 'EVTH', 'EVTE', 'RUNE', 'LONG', 'DATB'

7.2 Particle Data Sub-block (7 words/particle, up to 39 particles/sub-block)

  Word no.   Content
  7(n-1)+1  particle code: particle_id × 1000 + hadr_gen × 10 + obs_level
            or PID×1000 + 102 (muon additional information)
  7(n-1)+2  px  momentum x component (GeV/c)
  7(n-1)+3  py  momentum y component (GeV/c)
  7(n-1)+4  pz  momentum z component (GeV/c, downward positive)
  7(n-1)+5  x  lateral coordinate (cm)
  7(n-1)+6  y  lateral coordinate (cm)
  7(n-1)+7  t  arrival time (ns, measured from first interaction or atmospheric entry)

  In thinning mode an 8th word is added for the weight.

  Muon additional information (MUADDI T): a parent-particle information block is
  appended after the muon data block.
  EHISTORY option: adds a grandparent-particle information block.

7.3 Key Event-Header Sub-block (EVTH) Fields

  Word no.  Content
  1      'EVTH'
  2      event number
  3      primary particle ID
  4      primary total energy (GeV)
  5      starting atmospheric depth (g/cm²)
  6      target nucleus of first interaction
  7      first-interaction height (cm, negative value means tracked from the top of the atmosphere)
  8      px momentum x (GeV/c)
  9      py momentum y (GeV/c)
  10     pz momentum z (GeV/c, downward positive)
  11     zenith angle θ (rad)
  12     azimuth angle φ (rad)
  44     run number
  45     date (yymmdd)
  79     CURVED flag (0=standard, 2=CURVED)
  81-82  θ interval (degrees)
  83-84  φ interval (degrees)
  139    SIBYLL version flag
  141    QGSJET version flag
  168    CURVOUT flag (0=planar, 1=curved)

================================================================================
8. Particle Code Table
================================================================================

  ID        Particle
  1         γ (photon)
  2         e⁺
  3         e⁻
  4         ν_e (electron neutrino)
  5         μ⁺
  6         μ⁻
  7         π⁰
  8         π⁺
  9         π⁻
  10        K_L⁰ (long-lived neutral kaon)
  11        K⁺
  12        K⁻
  13        n (neutron)
  14        p (proton)
  15        K_S⁰ (short-lived neutral kaon)
  16-23     Δ baryons
  24-29     Σ baryons
  30-31     Ξ baryons
  32        Λ
  33        Ω⁻
  34-37     antibaryons
  38-55     ρ, ω, η and other mesons
  56-59     D mesons
  60-63     Λ_c charmed baryons
  64-65     not yet used
  66-70     J/ψ, ψ'
  71-76     τ, ν_τ
  77-80     B mesons
  81-91     ??
  92        π⁰ or nuclear fragment
  93        nuclear fragment (>1 nucleon)
  94        nuclear fragment (0 nucleons)
  95        Cherenkov photon
  96        neutrino (category not distinguishable)
  97        stopped particle

  Nuclei: ID = A × 100 + Z (e.g. ⁵⁶Fe²⁶ → 5626, ¹⁶O⁸ → 1608)

================================================================================
9. Coordinate Systems
================================================================================

9.1 Standard Coordinate System

  - Origin: sea level (OBSLEV=0) or the first observation level
  - x axis: points to magnetic north
  - y axis: points to west
  - z axis: vertically upward
  - Momentum pz sign: downward is positive (i.e. along -z)
  - Zenith angle θ: relative to the -z axis (vertically downward = 0°)
  - Azimuth angle φ: measured counterclockwise from magnetic north (+x axis = 0°, +y = 90°)

9.2 CURVED-Mode Coordinate System

  Uses a sliding planar atmosphere:
  - local coordinate-system origin at the detector position (sea level)
  - particle coordinates are tracked in the local Cartesian system; the coordinate
    system is rotated after each step
  - OUTPAR(5), OUTPAR(6) = lateral position of the particle upon reaching the
    observation level (cm)
    i.e. the lateral distance relative to the detector (the projection of the shower
    core onto the ground)
  - CORRXY correction: CORSIKA applies a geometric correction to the curved projection
  - XOFF/YOFF: participate in offset subtraction only in non-CURVED modes

9.3 INCLINED Mode

  Inclined observation-plane mode, defined by the INCLIN card:
  - the plane can be defined perpendicular to the shower axis (automatic mode) or with
    a user-defined orientation
  - output coordinates are within the inclined plane; (X=0,Y=0) corresponds to the
    shower-axis intersection point

================================================================================
10. Utilities
================================================================================

10.1 COAST Library (C++ Data Analysis)

  C++ toolkit under the coast/ directory:
    - read DAT binary particle output
    - Python (NumPy), ROOT, ASCII output
    - file merging (CorsikaMerge)
    - custom analysis interface (COASTUSERLIB)

  Main tool paths:
    src/utils/coast/CorsikaRead/   # particle reader
    src/utils/coast/CorsikaMerge/  # file merging
    src/utils/coast/rootout/       # ROOT output
    src/utils/coast/dat2npy/       # → NumPy format

10.2 Fortran Utilities (src/utils/)

  - readcsk2asci.f        binary → ASCII conversion
  - corsikaread.f         binary reading and printing
  - corsikahisto.f        two-dimensional histogram output
  - corsplitevts.f        file splitting (by event)
  - sumlongifiles.f       longitudinal file merging
  - bcreinpcont.f         automatically generate continued input cards

10.3 GDAS Utility

  src/utils/gdastool  — generate ATMFILE-format atmosphere profiles from the GDAS database.

10.4 Python / Shell

  - dat2npy → Python/NumPy format
  - readcsk2prtcls.sh → split by particle type

================================================================================
11. Common Issues and Recommendations
================================================================================

11.1 NKG Automatically Disabled in CURVED Mode

  In the CURVED build the FNKG flag of ELMFLG can be set to T, but the NKG analytic
  formula is disabled internally. This does not affect the EGS4 treatment of the
  electromagnetic component.

11.2 Energy-Threshold Effects at Large Zenith Angles

  For inclined incidence the atmospheric slant depth increases substantially (about
  3860 g/cm² at 75° vs about 1036 g/cm² at 0°), which raises the minimum energy for
  muons to reach the ground. To study the inclined flux of low-energy muons, it is
  recommended to set the EMU parameter of ECUTS below the target threshold.

11.3 Controlling Output File Size

  High-energy showers produce an enormous number of particles. Recommendations:
  - use THIN thinning (see Section 4.10)
  - use CORECUT to suppress near-axis particles
  - use PAROUT for selective output
  - AUGERHIT option (records only particles near the detectors)

11.4 Seeds and Statistical Independence

  Using a different seed (first SEED argument) for each run yields independent events.
  Within each event, advancing seeds guarantee sequence uniqueness.
  Note that each event requires at least 2 outer sequences (hadronic + EGS4).

11.5 Choosing the Energy Cuts ECUTS

  Low cuts record more particles but produce huge files; high cuts lose information.
  For muons, EMU≥0.3 GeV is recommended; for e/γ, ≥0.003 GeV is recommended.
  Note: parent particles (π, K) are not tracked below the ECUT; if they should decay
  into low-energy muons, the hadronic cut EHAD must be lowered.

11.6 Mixed Primary Spectra

  The COMBINE card can combine several primary particle types and spectral shapes.
  Alternatively, run batches independently for different primaries and merge them with
  weights.

11.7 References

  When publishing, it is recommended to cite:
  - D. Heck et al., Report FZKA 6019 (1998)
  - CORSIKA official website: https://www.iap.kit.edu/corsika/


================================================================================
  End of document  |  Compiled from CORSIKA_GUIDE7.8010.pdf (207 pages) + README
================================================================================
