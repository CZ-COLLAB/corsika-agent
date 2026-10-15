================================================================================
  CORSIKA 7.8010 Usage Summary
  Based on CORSIKA_GUIDE7.8010.pdf (207 pages, 2025-04-03) + README
================================================================================

Contents:
  1. Overview
  2. Installation and Compilation
  3. Important Compilation Options
  4. Input Control Cards in Detail
     4.1 Run Identification and Random Numbers
     4.2 Primary Particles and Energy
     4.3 Angle Definitions
     4.4 Observation Height and Energy Cutoffs
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
     7.2 Particle Data Sub-blocks (7 words/particle)
     7.3 Key Event-Header Sub-block Fields
  8. Particle Code Table
  9. Coordinate Systems
  10. Practical Tools
  11. FAQ and Recommendations


================================================================================
1. Overview
================================================================================

CORSIKA (COsmic Ray SImulations for KAscade) is a detailed simulation program for
extensive air showers (EAS) developed by KIT (Karlsruhe Institute of Technology),
Germany. It simulates the cascade processes triggered when high-energy cosmic-ray
particles enter the atmosphere, and records the various secondary particles reaching
the observation level (γ, e±, μ±, hadrons, neutrinos, etc.). It is widely used for:

  - Large ground-based experiments: Auger, IceCube/IceTop, KASCADE, HAWC, LHAASO, etc.
  - Atmospheric Cherenkov telescopes: H.E.S.S., MAGIC, VERITAS, CTA
  - Neutrino astronomy: atmospheric neutrino background studies

Energy range: ~10^11 eV to ~10^20 eV
Current version: 7.8010 (2025-04-03)


================================================================================
2. Installation and Compilation
================================================================================

2.1 Obtaining the source code

From the KIT server (password required):
  https://web.iap.kit.edu/corsika/download/
  username: corsika
  go to corsika-v780/ → corsika-78010.tar.gz

2.2 Installation steps

  tar xzf corsika-78010.tar.gz
  cd corsika-78010
  ./coconut                          # interactive install with no arguments

  # or pipe preset options (non-interactive):
  # echo "corsika-78010/install_script.inp" | ./coconut

2.3 Coconut interactive notes

coconut asks the following in order:
  a) operating system type (Linux, MacOS, etc.)
  b) Fortran compiler (gfortran, ifort, etc.)
  c) whether MPI parallelism is needed (PARALLEL)
  d) whether to enter expert mode — YES recommended, allows customizing compile options
  e) select the program options to enable (see Section 3)
  f) hadronic interaction model selection

In expert mode each feature can be toggled individually. After compilation, the
executable corsika and utility programs are in the run/ directory.

2.4 Basic data files

The run/ directory must contain the following data files (downloaded or copied
automatically at compile time):
  - NUCNUCCS                   nucleus-nucleus/nucleus-nucleon cross-section data
  - EGSDAT6_x.x                electromagnetic interaction data (EGS4)
  - hadronic model cross-section data: qgsdat-II-04, sectnu-II-04, etc.
  - VENUSDAT (VENUS model)
  - UrQMD-*-xs.dat (UrQMD model)


================================================================================
3. Important Compilation Options
================================================================================

The following options must be selected during coconut installation (expert mode):

| Option name    | Description                                             |
|---------------|---------------------------------------------------------|
| CURVED        | Curved-atmosphere version, supports large zenith angles (>70°) up to nearly 90° |
| THIN          | Statistical thinning, reduces particle output for high-energy showers |
| THINMAX       | Enhanced THIN; all thinned particles kept at the maximum weight |
| MULTITHIN     | Multiple thinning, supports up to 6 independent thinning parameter sets |
| CERENKOV      | Cherenkov photon simulation                             |
| IACT          | Imaging atmospheric Cherenkov telescopes (MAGIC, HESS, CTA) |
| ATMEXT        | External atmosphere models (MODTRAN, GDAS)              |
| SLANT         | Slant-depth longitudinal distribution                   |
| UPWARD        | Upward-going particles (neutrinos, τ leptons)           |
| EHISTORY      | Additional mother/grandmother particle history output   |
| MUPROD        | Track detailed muon production information              |
| ROOTOUT       | Direct ROOT output (recommended to convert via COAST post-processing) |
| COMPACT       | Compressed particle output format                       |
| INCLINED      | Inclined observation plane                              |
| NUPRIM        | Primary neutrino mode                                   |
| CHARM/TAULEP  | Charm particle / τ lepton production and decay          |
| PRESHOWER     | Pre-showering of ultra-high-energy γ                    |
| CONEX         | Fast simulation with cascade equations (hybrid with full CORSIKA simulation) |
| PARALLEL      | MPI parallelism                                         |
| COASTUSERLIB  | COAST user-library interface                            |
| COREAS        | Radio emission simulation                               |

Note: CURVED and CONEX cannot be enabled simultaneously (CONEX internally uses part
of the CURVED code).


================================================================================
4. Input Control Cards in Detail
================================================================================

Control-card format:
  KEYWRD  arg1  arg2  ...  [comment]
  Keywords left-aligned (≤6 characters), arguments space-separated, up to 512 columns.
  Comment lines: first character c/C + space, or *.
  Case-insensitive (except character parameters such as EPOPAR/DATDIR/DIRECT).

================================================================================
4.1 Run Identification and Random Numbers
================================================================================

RUNNR   NRRUN              format (A5, I)  default 1
  Run number, used to generate the output filename (DATnnnnnn).
  Range: 0 ≤ NRRUN ≤ 999999 (NRREXT option: 0~999999999)

EVTNR   SHOWNO             format (A5, I)  default 1
  Starting event number; subsequent events increment automatically.

SEED    ISEED1 ISEED2 ISEED3   format (A4, 3I)
  Random-number seed sequence k (assigned in order of appearance):
    k=1: hadronic showers
    k=2: EGS4 electromagnetic part
    k=3: Cherenkov photons
    k=4: IACT/AUGERHIT offset
  At least seeds k=1,2 are required. Changing ISEED1 alone yields a different sequence.
  ISEED2/3 are used to skip over many random-number calls, consuming lots of CPU;
  not recommended.
  Limit: 1 ≤ ISEED1 ≤ 900,000,000

  # Typical example:
  SEED 12345 0 0
  SEED 67890 0 0

================================================================================
4.2 Primary Particles and Energy
================================================================================

NSHOW   NSHOW              format (A5, I)  default 10
  Number of showers generated per run. NSHOW ≥ 1

PRMPAR  ID                 format (A6, I)  default 14
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

ERANGE  LLIMIT  ULIMIT     format (A6, 2F)  default 1.E4, 1.E4
  Total primary energy range (GeV, including rest mass).
  If LLIMIT = ULIMIT the energy is fixed.
  Recommended upper limits: HDPM 1E8, VENUS 2E7, DPMJET 1E10.

ESLOPE  PSLOPE             format (A6, F)  default 0.
  Spectral index γ, spectrum dN/dE ∝ E^γ.
  Ineffective for fixed energy.

================================================================================
4.3 Angle Definitions
================================================================================

THETAP  THMIN  THMAX       format (A6, 2F)  default 0., 0.
  Primary zenith-angle range (degrees). Within the range, angles are drawn from a
  sinθ·cosθ distribution (the detection rate of a horizontal detector under a
  uniform isotropic flux).
  Standard mode limit: THETPR(i) ≤ 70°
  CURVED mode limit: THETPR(i) < 90°
  If THMIN = THMAX the angle is fixed.

PHIP    PHMIN  PHMAX       format (A4, 2F)  default 0., 0.
  Azimuth-angle range (degrees). ϕ=0° points to magnetic north, ϕ=90° to west.
  Range: -360° ≤ PHIPR(i) ≤ 360°

================================================================================
4.4 Observation Height and Energy Cutoffs
================================================================================

OBSLEV  HEIGHT             format (A6, F)  default 110.E2 (cm, i.e. 110 m a.s.l.)
  Observation height (cm a.s.l.). Up to 10 observation levels (each call defines one).
  Only 1 observation level in CURVED mode.
  Set 0. for sea level.

ECUTS   EHAD  EMU  EELEC  EGAM   format (A5, 4F)  default 0.3, 0.3, 0.003, 0.003
  Particle kinetic-energy cutoffs (GeV); particles below these values are discarded:
    EHAD: hadrons (except π⁰), per nucleon for nuclei
    EMU:  μ⁺/μ⁻
    EELEC: e⁺/e⁻ (also the NKG computation threshold; recommended < 0.08 GeV)
    EGAM: photons
  Limits: EHAD≥0.05, EMU≥0.01, EELEC/EGAM≥0.00005

================================================================================
4.5 Hadronic Interaction Models
================================================================================

High-energy models (select one primary model, set the rest to F):

  SIBYLL  F  DEBUGLEV     format (A6, L, I)  default T, 0
     Enables the SIBYLL 2.3d/e model, default T. DEBUGLEV: debug level.

  SIBSIG  F               format (A6, L)     default T
     Use SIBYLL cross sections.

  QGSJET  F  DEBUGLEV     format (A6, L, I)  default T, 0
     QGSJET-II-04 or QGSJET01d (depending on compile options).

  EPOS    F  DEBUGLEV     format (A5, L, I)  default T, 0
     EPOS LHC model.

  DPMJET  F  DEBUGLEV     format (A6, L, I)  default T, 0
     DPMJETIII model.

  FLUKA   F               format (A5, L)     default T
     Low-energy hadronic model (requires the FLUKA interface at compile time).

  GHEISHA F               format (A7, L)     default T
     Built-in low-energy hadronic model (GHEISHA 2002).

  Note: switching between high-energy models is not mutually exclusive, but only one
        is actually used. The high/low transition energy is set by the HILOW card
        (default 80 GeV).

================================================================================
4.6 Electromagnetic Interactions
================================================================================

ELMFLG  FNKG  FEGS        format (A6, 2L)   default T, T
  FNKG: use the NKG analytic formula for electromagnetic sub-showers
       (automatically disabled in CURVED mode, where curvature invalidates the formula)
  FEGS: use EGS4 for the exact simulation of e⁺/e⁻/γ electromagnetic cascades
  # Usually both are set to T (both handled simultaneously)
  # If only the muon flux matters, set FNKG=F, FEGS=T to speed up the simulation

================================================================================
4.7 Atmosphere Models
================================================================================

ATMOD   MODATM             format (A5, I)   default 1
  Atmosphere model number:
    0  = user-defined (requires ATMA/ATMB/ATMC/ATMLAY to be set)
    1  = US standard atmosphere (Linsley parametrization) [default]
    2~8 = central-European atmospheres by month (Ulrich)
    11~16 = Antarctic atmosphere (MSIS-90-E, Lipari)
    17 = US standard atmosphere (Keilhauer parametrization)
    18~29 = Malargüe, Argentina atmospheres by month (Auger experiment)
    30~41 = Antarctic IceTop atmospheres by month (de Ridder)

ATMA    A1 A2 A3 A4 [A5]    format (A4, 4F or 5F)
ATMB    B1 B2 B3 B4          format (A4, 4F)
ATMC    C1 C2 C3 C4 [C5]    format (A4, 4F or 5F)
  Atmosphere parameters, only used for ATMOD=0 or 10.
  Formulas: t(h) = A_i + B_i * exp(-h/C_i)  (layers 1-4)
            t(h) = A_5 - h/C_5               (layer 5 linear approximation)

ATMLAY  H2 H3 H4 H5         format (A6, 4F)   default 4.E5, 10.E5, 40.E5, 100.E5 (cm)
  Layer boundary heights, only used for ATMOD=0 or 10.

ATMOSPHERE  IATMO  FREFR   format (A10, I, L) default 0, F
  Use a MODTRAN external atmosphere (requires the ATMEXT compile option).
  IATMO=1~6: tropical/mid-latitude summer & winter/sub-arctic summer & winter/US standard
  FREFR: whether to account for atmospheric refraction (Cherenkov photons)

ATMFILE  FILENAME         format (A7, A1024)
  Read the atmosphere profile from a fit file of the GDAS database; generated with
  the gdastool utility.

================================================================================
4.8 Geomagnetic Field
================================================================================

MAGNET  BX  BZ             format (A6, 2F)   default 20.40, 43.23 (μT, Karlsruhe)
  BX: horizontal component (pointing north, μT)
  BZ: vertical component (downward, μT)
  Obtainable online with the Geomag program: https://www.ngdc.noaa.gov/geomag/calculators/

================================================================================
4.9 Output Control
================================================================================

DIRECT  PATH               format (A6, A239)
  Output directory path. Lowercase is not automatically converted to uppercase.
  PATH must not start with ~. Current directory: DIRECT ./

PAROUT  FPAROUT  FTABOUT   format (A6, 2L)   default T, F
  FPAROUT: whether to write the particle output file (DATnnnnnn)
  FTABOUT: whether to write the table output (DATnnnnnn.tab)

DATBAS  F                  format (A6, L)     default F
  Whether to write the DATnnnnnn.dbase database summary file.

LONGI   FLONG  STEPS  FTABLE  FOUT   format (A5, L, F, L, L)
  Longitudinal development output control.
  STEPS: output once every STEPS g/cm².

FLONGOUT  F                format (A8, L)     default F
  Write longitudinal information into the LONG block of the DAT particle output file.

MAXPRT  N                  format (A6, I)     default 1
  Print detailed logs for the first N showers; summaries only afterwards.

================================================================================
4.10 Thinning (THIN)
================================================================================

THIN    EFRCTHN  WMAX  RMAX   format (A4, 3F)   default 1.E-4, 1.E30, 0.E0
  EFRCTHN: energy-fraction threshold (relative to the primary energy); particles
           below it are thinned
  WMAX:    maximum weight. Particles whose weight exceeds it are no longer thinned
  RMAX:    radial thinning radius (cm); 0 disables radial thinning
           (particles within r < RMAX are kept with probability (r/RMAX)^4)
  Typical setting: THIN 1.E-6 1.E3 0.

THINH   THINRAT  WEITRAT      format (A5, 2F)   default 1., 1.
  Hadron thinning parameter overrides:
  THINRAT: ε_em/ε_had (electromagnetic/hadronic energy-fraction ratio)
  WEITRAT: WMAX_em/WMAX_had

THINEM  THINRAT  WEITRAT      format (A6, 2F)   default 1., 1.
  Electromagnetic thinning parameter overrides (mutually exclusive with THINH).

Thinning efficiency reference (10^15 eV, QGSJET):
  EFRCTHN  time(min)  particle count
  none     98        413078
  1E-6     51        58313
  1E-5     7.2       11466
  1E-4     1.2       2211
  1E-3     0.16      419

================================================================================
4.11 Other Common Cards
================================================================================

FIXCHI  THICK0             format (A6, F)     default 0.
  Starting atmospheric depth (g/cm²). The primary starts at this vertical depth.
  Mutually exclusive with FIXHEI.

FIXHEI  HEIGHT  N1STTR    format (A6, F, I)  default 0., 0
  Fixed first-interaction height (cm). N1STTR=1/2/3 specifies the target-nucleus type.

HADFLG  NFLAIN NFLDIF NFLPI0 NFLPIF NFLCHE NFRAGM   format (A6, 6I)
  Hadronic interaction parameters:
  NFRAGM=2 [default]: sequential fragmentation (experimental pT)
  NFRAGM=0: complete fragmentation into free nucleons
  NFRAGM>2: different fragmentation models

STEPFC  F                  format (A6, F)     default 1.
  EGS4 electromagnetic step-size scaling factor.

RADNKG  R                  format (A6, F)     default 200.E2 (cm)
  Maximum distance of the NKG lateral distribution.

MUMULT  F                  format (A6, L)     default T
  Muon multiple scattering (Molière or Gauss).

MUADDI  F                  format (A6, L)     default F
  Output additional muon information (mother-particle information).

ARRANG  ANGLE              format (A6, F)     default 0.
  Angle between the detector-array x axis and magnetic north (degrees).

ECTMAP  E                  format (A6, F)     default 1.E2 (GeV)
  Energy threshold for printed output — affects only .lst output, not particle output.

CURVOUT F                  format (A7, L)     default T (CURVED mode)
  In CURVED mode the observation level follows Earth's curvature. If F, planar
  approximation is used.

EXIT                        format (A4)
  Must be the last card; marks the end of input.


================================================================================
5. CURVED Mode
================================================================================

5.1 When to use

  CURVED mode is required for zenith angles >70° (standard mode limits THETAP ≤70°).
  CURVED mode treats Earth as a sphere of radius 6371.315 km, using the "sliding
  plane" approximation: the particle trajectory is discretized into steps in a
  succession of local Cartesian systems; after each step the coordinate system is
  rotated so that the z axis points again toward the geocenter.

5.2 Main differences from standard mode

  - THETAP upper limit extended from 70° to <90° (up to 180° combined with UPWARD)
  - NKG formulas automatically disabled (spherical geometry not applicable)
  - only 1 observation level supported
  - output coordinates are lateral distances in the detector system (see Section 9)
  - lateral coordinates corrected by CORRXY (spherical projection correction)

5.3 The CURVOUT card

  CURVOUT F (default T):
    T: observation level is spherical (follows Earth's curvature); output coordinates
       (X', Y') can be converted back to true (X, Y, Z) via spherical geometry
    F: observation level is a planar approximation, tracking only up to height
       Z=OBSLEV(1)
    Forced to T between 85° and 95°.


================================================================================
6. Running Methods and Examples
================================================================================

6.1 Run command

  ./corsika < input_file  [> output.lst]
  # input_file is a text control-card file

  Example:
  ./corsika < all-inputs-SIBYLL3 >& DAT000042.lst

6.2 Minimal input-file example

  ----------------------------------------------------------------
  RUNNR   42          ! run number
  EVTNR   1           ! starting event number
  SEED    12345 0 0   ! hadronic shower seed
  SEED    67890 0 0   ! EGS4 seed
  NSHOW   10000       ! number of showers
  PRMPAR  14          ! proton
  ERANGE  1.  1.E5    ! fixed energy (1 TeV)
  THETAP  0.  89.     ! zenith angle 0°~89°
  PHIP    -180. 180.  ! full azimuthal range
  SIBYLL  T  0        ! SIBYLL 2.3e model
  SIBSIG  T           ! SIBYLL cross sections
  ELMFLG  T  T        ! NKG + EGS4
  ECUTS   0.3  0.3  0.003  0.003  ! energy cutoffs
  OBSLEV  0.          ! sea-level observation
  DIRECT  ./          ! output to current directory
  EXIT                ! end
  ----------------------------------------------------------------

6.3 THIN example

  ----------------------------------------------------------------
  THIN    1.E-6  1.E3  0.    ! thin at 1E-6 of primary energy, max weight 1000
  THINH   1.     100.        ! hadron weight ratio 100 (muons stay exact)
  ----------------------------------------------------------------


================================================================================
7. DAT Binary Output Format
================================================================================

7.1 Block structure

A DAT file is Fortran sequential unformatted binary, default block length 22932 bytes
(= 5733 words × 4 bytes, each large block = 21 sub-blocks × 273 words).

                    repeated per shower →
  ┌─────────┬──────────┬────┬──────┬────┬──────┬──────────┐
  │ RUNH    │ EVTH  #1 │DATA│ DATA │... │ EVTE │ EVTH  #2 │...
  │ (run header) │ (event header) │    │      │    │(event trailer)│ (event header) │
  └─────────┴──────────┴────┴──────┴────┴──────┴──────────┘

  End of file:
  RUNE (run trailer)

  Each sub-block starts with a 4-character identifier: 'RUNH', 'EVTH', 'EVTE', 'RUNE',
  'LONG', 'DATB'

7.2 Particle data sub-blocks (7 words/particle, up to 39 particles/sub-block)

  Word       Content
  7(n-1)+1  particle code: particle_id × 1000 + hadr_gen × 10 + obs_level
            or PID×1000 + 102 (additional muon information)
  7(n-1)+2  px, x momentum component (GeV/c)
  7(n-1)+3  py, y momentum component (GeV/c)
  7(n-1)+4  pz, z momentum component (GeV/c, positive downward)
  7(n-1)+5  x lateral coordinate (cm)
  7(n-1)+6  y lateral coordinate (cm)
  7(n-1)+7  t arrival time (ns, from first interaction or atmospheric entry)

  In thinning mode an 8th word is added per particle, holding the weight.

  Additional muon information (MUADDI T): mother-particle information blocks follow
  the muon data blocks.
  EHISTORY option: adds grandmother-particle information blocks.

7.3 Key event-header sub-block (EVTH) fields

  Word    Content
  1      'EVTH'
  2      event number
  3      primary particle ID
  4      primary total energy (GeV)
  5      starting atmospheric depth (g/cm²)
  6      first-interaction target nucleus
  7      first-interaction height (cm, negative means tracked from the top of the atmosphere)
  8      px momentum x (GeV/c)
  9      py momentum y (GeV/c)
  10     pz momentum z (GeV/c, positive downward)
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
  34-37     anti-baryons
  38-55     ρ, ω, η and other mesons
  56-59     D mesons
  60-63     Λ_c charm baryons
  64-65     not yet used
  66-70     J/ψ, ψ'
  71-76     τ, ν_τ
  77-80     B mesons
  81-91     ??
  92        π⁰ or nuclear fragment
  93        nuclear fragment (>1 nucleon)
  94        nuclear fragment (0 nucleons)
  95        Cherenkov photon
  96        neutrino (undistinguishable type)
  97        particle at rest

  Nuclei: ID = A × 100 + Z (e.g. ⁵⁶Fe²⁶ → 5626, ¹⁶O⁸ → 1608)


================================================================================
9. Coordinate Systems
================================================================================

9.1 Standard coordinate system

  - Origin: sea level (OBSLEV=0) or the first observation level
  - x axis: toward magnetic north
  - y axis: toward west
  - z axis: vertically upward
  - Momentum pz sign: positive downward (i.e. along the -z direction)
  - Zenith angle θ: relative to the -z axis (straight downward is 0°)
  - Azimuth angle φ: measured counterclockwise from magnetic north (along +x is 0°, +y is 90°)

9.2 CURVED-mode coordinate system

  Uses the sliding planar atmosphere:
  - the local coordinate-system origin is at the detector position (sea level)
  - particle coordinates are tracked in the local Cartesian system; the coordinate
    system is rotated after each step
  - OUTPAR(5), OUTPAR(6) = lateral position (cm) of the particle reaching the
    observation level, i.e. the lateral distance relative to the detector
    (the core's projection on the ground)
  - CORRXY correction: CORSIKA applies a geometric correction for the curved projection
  - XOFF/YOFF: participate in the offset subtraction only in non-CURVED mode

9.3 INCLINED mode

  Inclined observation-plane mode, defined by the INCLIN card:
  - can define a plane perpendicular to the shower axis (automatic mode) or a
    user-defined orientation
  - output coordinates are in the inclined plane, with (X=0,Y=0) at the shower-axis
    intersection


================================================================================
10. Practical Tools
================================================================================

10.1 COAST library (C++ data analysis)

  C++ toolkit in the coast/ directory:
    - reads DAT binary particle output
    - Python (NumPy), ROOT, ASCII output
    - file merging (CorsikaMerge)
    - custom analysis interface (COASTUSERLIB)

  Main tool paths:
    src/utils/coast/CorsikaRead/   # particle reader
    src/utils/coast/CorsikaMerge/  # file merging
    src/utils/coast/rootout/       # ROOT output
    src/utils/coast/dat2npy/       # → NumPy format

10.2 Fortran tools (src/utils/)

  - readcsk2asci.f        binary → ASCII conversion
  - corsikaread.f         binary reading and printing
  - corsikahisto.f        two-dimensional histogram output
  - corsplitevts.f        file splitting (by event)
  - sumlongifiles.f       longitudinal file merging
  - bcreinpcont.f         automatic generation of continuous input cards

10.3 GDAS tools

  src/utils/gdastool  — generates ATMFILE-format atmosphere profiles from the
  GDAS database.

10.4 Python / Shell

  - dat2npy → Python/NumPy format
  - readcsk2prtcls.sh → split by particle type


================================================================================
11. FAQ and Recommendations
================================================================================

11.1 NKG automatically disabled in CURVED mode

  In the CURVED build the FNKG flag of ELMFLG can still be set to T, but the NKG
  analytic formula is automatically disabled internally. This does not affect the
  EGS4 handling of the electromagnetic component.

11.2 Energy-threshold effects at large zenith angles

  At inclined incidence the atmospheric slant depth increases greatly (75° ≈ 3860 g/cm²
  vs 0° ≈ 1036 g/cm²), raising the minimum muon arrival energy. To study the inclined
  flux of low-energy muons, set the EMU parameter of ECUTS below the target threshold.

11.3 Controlling the output file size

  High-energy showers contain a huge number of particles. Recommendations:
  - use THIN thinning (see Section 4.10)
  - use CORECUT to mask near-axis particles
  - use PAROUT for selective output
  - the AUGERHIT option (records only particles near the detector)

11.4 Seeds and statistical independence

  Using a different seed (first SEED parameter) per run produces independent showers.
  Within each shower, progressive seeding guarantees unique sequences.
  Note that each shower needs at least 2 external sequences (hadronic + EGS4).

11.5 Choosing the ECUTS energy cutoffs

  Low cutoffs record more particles but produce huge files; high cutoffs lose information.
  Recommended: EMU≥0.3 GeV for muons, ≥0.003 GeV for e/γ.
  Note: mother particles (π, K) below ECUT are not tracked; if they should decay into
  low-energy muons, lower the hadronic cutoff EHAD.

11.6 Mixed primary spectra

  The COMBINE card can combine multiple primary particle types and spectral shapes.
  Alternatively, run different primaries independently in batch and combine with weights.

11.7 References

  For publications, recommended citations:
  - D. Heck et al., Report FZKA 6019 (1998)
  - CORSIKA website: https://www.iap.kit.edu/corsika/


================================================================================
  End of document  |  Based on CORSIKA_GUIDE7.8010.pdf (207 pages) + README
================================================================================
