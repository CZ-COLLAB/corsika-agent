# Plan: CORSIKA simulation of sea-level 0° / 75° muon differential flux

Goal: reproduce *A Comparison of Muon Flux Models at Sea Level* (fenrg-09-750159)
Figure 2 — x-axis muon momentum/kinetic energy (1–1000 GeV), y-axis differential intensity
dN/(dE dA dΩ dt) [cm⁻² s⁻¹ sr⁻¹ GeV⁻¹], two curves θ=0°(A) and θ=75°(B).

---

## 1. Physical quantity to compute

Sea-level muon differential intensity (per unit energy·area·solid angle·time):

    I_μ(E_μ, θ) = dN_μ / (dE_μ dA dΩ dt)   [cm⁻² s⁻¹ sr⁻¹ GeV⁻¹]

Paper conventions (consistent with Figure 2):
- θ=0°: count muons with θ_μ < 7°, ΔΩ₀ = 2π(1−cos7°) ≈ 0.0467 sr
- θ=75°: count 70° < θ_μ < 80°, ΔΩ₇₅ = 2π(cos70°−cos80°) ≈ 1.058 sr

Muon variables: in the `data_1` NTuple output by CORSIKA's `CorsikaPlottermini`,
`ek` is kinetic energy, `px,py,pz` give θ_μ = arccos(pz/|p|). The paper's x-axis
uses kinetic energy; we bin directly in `ek` (or use momentum
p = √((ek+m)²−m²), m=0.1057 GeV).

## 2. Normalization formula (key)

For each primary energy point E_k (logarithmic grid), run N_show,k showers (fixed
zenith angle θ), and count in each shower the muons falling in [E_μ, E_μ+ΔE_μ]
and within the zenith-angle window ΔΩ: n_μ(E_k). The absolute differential flux
is the primary-spectrum-weighted sum:

    I_μ(E_μ, θ) = Σ_k [ Φ_p(E_k) · E_k · ΔlnE ] · [ n_μ(E_k) / (N_show,k · ΔE_μ · ΔΩ) ]

where Φ_p(E_k) is the primary cosmic-ray differential intensity
[cm⁻² s⁻¹ sr⁻¹ GeV⁻¹] (all components), and E_k·ΔlnE is the integration weight
of the log-equal grid (ΔlnE = ln(E_{k+1}/E_{k-1})/2).

Dimensional consistency: Φ_p [cm⁻² s⁻¹ sr⁻¹ GeV⁻¹] × (μ/primary/sr/GeV) = cm⁻² s⁻¹ sr⁻¹ GeV⁻¹.

Physical argument: muons reaching sea level with zenith angle θ_μ come mainly from
primaries with zenith angle ≈ θ_μ (narrow-cone approximation; see the θ_μ vs θ_primary
diagnostic in `run/diag_75deg.cc`). Hence for each θ it suffices to inject primaries
at fixed θ_p=θ.

## 3. Reusable existing infrastructure

- Binary: `run/corsika78010Linux_SIBYLL_urqmd`
  (`include/config.h` confirms `__CURVED__`, `__SIBYLL__`, `__URQMD__` are enabled;
  `__THIN__` is not → no thinning, muons exact and unweighted, exactly what is needed).
  75° requires CURVED, which this binary satisfies.
- DAT→ROOT: `run/CorsikaPlottermini`, producing the `Event` tree (Eprim, Theta)
  and the `data_1` TNtupleD (branches id, px, py, pz, x, y, ek, t, event_id).
- Existing scans: `run_muon_scan.sh`(75°) / `run_muon_scan_0deg.sh`(0°),
  energy points 1/10/100/1e3/1e4/1e5/1e6 GeV, 1 shower each.
  Reference results (total muons per shower, ECUTS=0.3):
    0°:   100→2, 1e3→6, 1e4→139, 1e5→1024, 1e6→12480
    75°:  1e3→2, 1e4→22, 1e5→211, 1e6→2122
  The existing scripts only count totals, do not bin in energy, and apply no
  primary-spectrum weighting, so the analysis must be extended.

## 4. CORSIKA steering card (one per run)

```
RUNNR   <n>
EVTNR   1
SEED    <s1> 0 0
SEED    <s2> 0 0
NSHOW   <N_show>            ! showers at this energy point
PRMPAR  <species>           ! 14=p, 402=He, 1408=N(CNO), 2814=Si, 5626=Fe
ERANGE  <E> <E>             ! fixed energy
THETAP  <θ> <θ>             ! 0. 0.  or  75. 75.
PHIP    -180. 180.
SIBYLL  T 0
SIBSIG  T
URQMD   T 0                 ! low-energy model, consistent with the existing binary
ELMFLG  T T                 ! under CURVED, NKG is automatically disabled; EGS4 unaffected
ECUTS   0.3  0.3  0.003 0.003   ! see note below
OBSLEV  0.                   ! sea level
MAGNET  20.40 43.23          ! default Karlsruhe (muons are little affected by geomagnetism; can be kept)
PAROUT  T F
DIRECT  <outdir>/
EXIT
```

Note (ECUTS, verified with a smoke test): the URQMD low-energy model forces
EHAD ≥ 0.3 GeV (source `corsika.F:19137` checks `ELCUT(1)<0.3 → error exit`),
hence EHAD=0.3. For the paper's 1–1000 GeV range, EMU=0.3 is sufficient: a
sea-level 1 GeV muon comes from the decay of a ~3 GeV π, whose parent is far
above the 0.3 GeV cutoff and is not discarded. If the range is ever extended to
<1 GeV muons, a low-energy model such as FLUKA (lower limit 0.02 GeV) is needed.

## 5. Primary cosmic-ray spectrum and composition

The absolute normalization depends on the primary spectrum. Suggested two steps:

- Step 1 (quick figure, validate the workflow): protons only, PRMPAR=14,
  energies 10 GeV–1e5 GeV, proton spectrum Φ_p(E) (power law
  ~1.8·(E/GeV)^−2.7 cm⁻² s⁻¹ sr⁻¹ GeV⁻¹, or the Hörandel Poly-gonato proton
  component). Protons dominate the <100 GeV muons.
- Step 2 (final calibration): full composition in 5 groups (p, He, CNO, MgSi, Fe),
  Hörandel (2003) Poly-gonato model for each Φ_i(E), run each group separately
  and combine with the formula weights. Heavy nuclei contribute more to
  high-energy muons and cannot be omitted.

The primary spectrum is the only "external input"; the final curves can be
absolutely compared with analytical models (Gaisser/Tang, Bugaev/Reyna) and the
Figure 2 red points to validate the chosen spectrum.

## 6. Simulation grid and statistics plan

Logarithmic energy grid (~4–6 points per decade), showers decreasing with the
increasing cost per energy:

| E_p (GeV)        | N_show/point | Remark |
|------------------|-----------|------|
| 1e1 – 1e2        | 2000–10000 | cheap, dominates the low-energy muon statistics |
| 1e2 – 1e3        | 1000–5000  | |
| 1e3 – 1e4        | 200–1000   | |
| 1e4 – 1e5        | 50–200     | |
| 1e5 – 1e6        | 10–50      | no THIN, large output, only fills the high-energy end |

- Fixed progressive seeds per point (only change the first SEED parameter) to
  keep all showers independent.
- For large batches: prefer HTCondor (see the `~/corsika_job/` template) or
  multi-process on the local machine; do not run serially on a login node.
- First a smoke test: 1 shower at 1e4 GeV for each of 0° and 75°, confirm the
  DAT/ROOT files are fine, the θ_μ distribution falls inside the window, and
  low-energy muons (ECUTS=0.05) really appear.

## 7. Analysis workflow (ROOT or Python)

1. Read the `Event` (Eprim, Theta) and `data_1` (id,px,py,pz,ek) of each `DAT*.root`.
2. Select id∈{5,6}, compute p=√(px²+py²+pz²), θ_μ=arccos(pz/p).
3. Zenith-angle windows: 0°→θ_μ<7°; 75°→70°<θ_μ<80°.
4. Fill a log histogram in ek (or p) (e.g. 0.3–3000 GeV, 10 bins per decade).
5. Normalize per energy point: n_μ/(N_show·ΔE_μ·ΔΩ), multiply by Φ_p(E_k)·E_k·ΔlnE and sum over E_k.
6. Obtain the two I_μ(E_μ) curves and plot them together with the analytical models / experimental points.

Reuse the existing macro style: `count_muons.C` (id criterion), `diag_75deg.cc`
(θ_μ computation); write a new `flux_hist.C` (or Python numpy reading ROOT) for
the weighted sum.

## 8. Comparison and validation (as a Figure 2 style plot)

- Main curves: CORSIKA results (0° blue, 75° red, log-log).
- Reference curves: Gaisser/Tang, Bugaev/Reyna analytical models (computed directly from the formulas).
- Optional: digitize and overlay the Figure 2 experimental red points
  (paper refs: 0° uses Achard/BESS/L3; 75° uses Jokisch/Kellogg/Tsuji).
- Acceptance criterion: CORSIKA curves agree with Gaisser/Tang, Bugaev/Reyna and
  the experimental points within ~20–30%; the 75° low-energy end should be
  clearly below 0° (attenuation/decay at slant depth ~4000 vs 1033 g/cm²).

## 9. Execution steps

1. Write two new steering-card templates + extend `run_muon_scan*.sh` (add NSHOW,
   ECUTS=0.05, multiple energy points, progressive seeds).
2. Smoke test (1 shower@1e4 GeV for each of 0°, 75°).
3. Small batch (~50 showers per point) to first get the shape and validate the
   workflow and θ windows.
4. Scale up statistics (per the §6 table), HTCondor/multi-process batches.
5. `flux_hist` weighted sum to get I_μ(E), compare and plot against analytical
   models / experimental data.
6. Archive everything in the workspace: cards, seeds, logs, DAT, analysis
   scripts, figures.

## 10. Main approximations and caveats

- The CURVED binary is used for both 0° and 75° (at 0° the curvature correction
  is negligible; kept for consistency).
- Narrow-cone approximation: muon zenith ≈ primary zenith; low-energy muons have
  larger angular spread, mostly covered within the ±5–7° windows.
- No THIN: above 1e5 GeV the output is large, so the number of showers must be
  controlled; for large sampling up to 1e6 GeV, compile a separate THIN build
  (`corsika78010Linux_SIBYLL_urqmd` + __THIN__ recompilation).
- The absolute normalization is sensitive to the primary spectrum; cross-check
  against experimental data / analytical models in the end.
- 75° low-energy muons have a minimum reachable energy (~a few GeV, from slant
  depth energy loss and decay), so the Figure 2B data start at ~10 GeV.
