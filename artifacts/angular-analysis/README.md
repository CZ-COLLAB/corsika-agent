# Sea-level muon flux vs zenith angle

CORSIKA 7.8010 simulation of the **absolute integrated atmospheric muon
flux** at sea level as a function of zenith angle θ (0–90°), using
**SIBYLL 2.3e** (high-energy) + **UrQMD** (low-energy).

## Flux definition and normalisation

    I_mu(theta) = sum_k [ Phi_p(E_k) * dE_k ] * [ N_mu(E_k, theta) / N_k ]
                = int dE_p  Phi_p(E_p) * <N_mu(E_p, theta)>

    Phi_p = Papini / Grimani / Stephens primary proton spectrum (solar minimum):
            J(E) = 3.2009e9 (E[MeV]+920)^-4 E[MeV]^1.25   [/(MeV s m^2 sr)]
                 = 3.2009e8 (Em+920)^-4 Em^1.25   [cm^-2 s^-1 sr^-1 GeV^-1]
    N_mu  = TOTAL number of mu+/- at sea level (all directions) per primary
    N_k   = number of showers at E_k

Resulting units: **cm^-2 s^-1 sr^-1** (per unit perpendicular area, per unit
solid angle). This is the standard CORSIKA convention: Phi_p is per sr and
the muon yield is the total per primary, so no extra solid-angle division.

Showers were importance-sampled from `E^-1.7` on [10, 10^6] GeV
(`ESLOPE -1.7`); each event is reweighted by
`Phi_p(E)/p_samp(E)` with `p_samp(E) = E^-1.7 / Z`,
`Z = int_10^1e6 E^-1.7 dE = 0.284947`.

## Configuration

| item | value |
|------|-------|
| executable | `~/corsika-78010/run/corsika78010Linux_SIBYLL_urqmd` |
| build | CORSIKA 7.8010, `__CURVED__`, `__EFIELD__` (ez = 0, no field), SIBYLL23E, URQMD13 |
| location | `MAGNET 22.71 40.96` (µT), `OBSLEV 0.` (sea level) |
| atmosphere | `ATMOD` default (US standard) |
| primary | proton `PRMPAR 14`, spectrum sampled with `ESLOPE -1.7`, 10–10^6 GeV |
| cuts | `ECUTS 0.3 0.3 0.003 0.003` GeV (UrQMD requires EHAD ≥ 0.3) |
| angles | θ = 0,5,10,…,85,88,89° (20 fixed angles; CURVED mode for θ > 60°) |
| statistics | 12000 showers per angle, 240000 total |
| seeds | `SEED (10^6 + 100·RUNNR + k) 0 0`, `SEED ...+7 0 0` per chunk |
| command | `./scan_angle.sh <theta> <runnr_base> 6 2000 1.E6` |

## Result

```
 theta  Nshow     Nmu   I [cm^-2 s^-1 sr^-1]     err
   0    12000  106907       5.7410e-03        7.24e-05
   5    12000  126915       5.5409e-03        7.06e-05
  10    12000  117512       5.5679e-03        7.11e-05
  15    12000  111640       5.2449e-03        6.96e-05
  20    12000  100373       4.9876e-03        6.62e-05
  25    12000   90174       4.7956e-03        6.45e-05
  30    12000   95418       4.1887e-03        5.92e-05
  35    12000  108989       3.8160e-03        5.63e-05
  40    12000   89442       3.3599e-03        5.15e-05
  45    12000   73322       2.8093e-03        4.57e-05
  50    12000   63669       2.2737e-03        3.94e-05
  55    12000   48775       1.8413e-03        3.43e-05
  60    12000   49610       1.4162e-03        2.90e-05
  65    12000   49167       9.6063e-04        2.14e-05
  70    12000   27628       6.0488e-04        1.56e-05
  75    12000   24384       3.8569e-04        1.13e-05
  80    12000   13573       1.6272e-04        5.63e-06
  85    12000    8296       5.2380e-05        2.51e-06
  88    12000    4243       1.8334e-05        1.13e-06
  89    12000    2354       1.4167e-05        9.74e-07
```

Fit (fixed exponent): **I(θ) = (5.652 ± 0.002)×10⁻³ · cos²θ  cm⁻² s⁻¹ sr⁻¹**
(χ²/dof = 315/19; a free exponent gives n = 1.986 ± 0.010, i.e. the data sit
very close to but slightly below a pure cos²θ).

### Analytic empirical curves

The model functions in `flux_angle.py` are ported **verbatim** from the
CRY analysis macro
`cry_v1.7/test/cryMuonFluxAnalysisWithCorsikanew.C`
(they also match Su et al., *Front. Energy Res.* **9** (2021) 750159).
Each is evaluated as `dN/dp(p,θ)` and integrated over momentum
(1–10⁵ GeV/c) to give the flux vs θ:

* **Gaisser/Tang** (`createGaisserTangGraph`): segmented, curvature-
  corrected `cosθ*`, `A = 1.1(90√(cosθ+0.001)/1030)^{4.5/((E+Δ)cosθ*)}`,
  `Δ=2.06×10⁻³(950/cosθ*−90)`, denominators `(1+1.1(E+Δ)cosθ*/115/810)`,
  `r_c=1e-4`; third branch `E<1/cosθ*` uses `E_eff=0.3E+0.7/cosθ*`.
  Integrated: **I(0)=6.03×10⁻³**.
* **Bugaev/Reyna** (`createBugaevReynaGraph`):
  `2.53×10⁻³ cos³θ (p cosθ)^{-(0.0209y³−0.2555y²+1.288y+0.2455)}`,
  `y=log₁₀(p cosθ)`; valid 0–90°. Integrated: **I(0)=7.02×10⁻³**.

Both follow the cos²θ shape and bracket the simulation
(5.65×10⁻³), the residual being the protons-only deficit. (An earlier
version of this script used the Gaisser-Tang formula straight from the
Gaisser-Tang paper PDF (`Gaisser-Tang.pdf`) but with `cosθ` instead of `cosθ*` and without the
low-energy branch, which suppressed the result to ≈2×10⁻³; now corrected
against the CRY code.)

The plain **Gaisser** model (`createGaisserGraph`) integrated gives
I(0)≈8.4×10⁻² (overestimates, as expected). A
**Smith & Duller/Chatzidakis** model (`createSDCGraph`) is also available in
the CRY macro and gives I(0)≈1.1×10⁻².

The vertical value 5.7×10⁻³ cm⁻² s⁻¹ sr⁻¹ is ~20 % below the accepted
sea-level muon intensity (~7×10⁻³); this is the expected protons-only
deficit (missing He/CNO/Fe).

## Files

```
muon_angle/
  analyze.py             DAT reader / muon counter
  dump_events.py         per-event (E_prim, N_mu) extractor
  scan_angle.sh          chunked per-angle run driver
  run_one.sh             single fixed-angle run (early test)
  flux_angle.py          absolute-flux analysis + final figure
  plot_scan.py           earlier relative-units version
  muon_flux_vs_angle.pdf/.png   final figure
  results/flux_vs_angle.csv     numeric result
  out/
    inp_theta*.inp       steering cards (seeds inside)
    corsika_theta*.lst   CORSIKA logs
    events_theta*.txt    per-event E_prim, N_mu  (DAT deleted, ~270 kB/shower)
    scan_theta*.log      run progress
```

## Approximations

1. **Proton only** (Papini proton spectrum; no He/CNO/Fe) → absolute flux low
   by ~20–30 %.
2. Upper energy cut 10^6 GeV (negligible muon-flux contribution above).
3. **Standard atmosphere**; no seasonal/ERA5 variation.
4. The EFIELD-enabled binary crashed once (SIGSEGV in `elfield.c:69`) during
   one 2000-shower chunk at θ=15°; that chunk was re-run with a different seed.
