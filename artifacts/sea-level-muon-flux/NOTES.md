# Run results and key findings (run1)

## Outputs

- `production/results/flux_0deg.csv` / `flux_75deg.csv`: differential flux I(E_μ) data
- `production/results/flux_compare_gaisser.png`: figure (CORSIKA points + Gaisser reference line)
- `production/out_0deg/`, `out_75deg/`: 42 DAT + ROOT files (14360 showers/angle)
- Scripts: `gen_jobs.py` (card generation), `run_batch.sh` (parallel runs), `analyze_flux.py` (weighting), `plot_figure2.py`

## Key numerical validation (0°, protons)

| E_μ (GeV) | CORSIKA | Reference value |
|---|---|---|
| 1   | 1.90e-3 | ~2e-3 (experimental data) |
| 10  | 1.61e-4 | ~2e-4 |
| 100 | 2.93e-7 | 3.13e-7 (Gaisser) |
| 1000| 2.13e-10| ~2e-10 |

75° is ~2 orders of magnitude below 0° at the low-energy end (attenuation/decay
at slant depth ~4000 vs 1033 g/cm²), consistent with Figure 2B.

## Pitfalls (important, reuse later)

1. **URQMD forces EHAD ≥ 0.3 GeV** (`corsika.F:19137`); ECUTS can only be `0.3 0.3 0.003 0.003`.
   Sufficient for the 1–1000 GeV range (the parent π of a 1 GeV sea-level muon is ~3 GeV, above the cutoff).
2. **CorsikaPlottermini multi-event file structure**: one `data_1;N` cycle per shower
   (`data_1;1`..`data_1;NSHOW`), and the `Event` tree has NSHOW entries.
   The analysis must iterate over all cycles (my first version only read `data_1;1`,
   underestimating the flux by ~NSHOW×).
3. **Primary spectrum normalization**: the proton differential spectrum used `Φ_p = 0.14 E^-2.7 cm^-2 s^-1 sr^-1 GeV^-1`
   (not the common 1.8). The 0.14 was fixed by three-point cross-validation:
   integrated total muon flux ~7e-3, Gaisser formula at 100 GeV = 3.13e-7,
   cosmic-ray integral intensity ~0.1 cm^-2 s^-1 sr^-1 (>1 GeV).
4. **The Theta in the Event tree is in radians** (75°→1.31 rad); computing θ_μ from pz/|p| in data_1 is more robust.
5. **~~Oblique incidence 1/cos²θ~~ (this conclusion is void, see 6)**
6. **The real normalization error: the solid angle ΔΩ was divided out once too often, and the muons must not be filtered by an angular window.**
   Correct formula (per unit perpendicular area, per unit solid angle):
   `I_μ(E_μ,θ) = Σ_k [Φ_p(E_k)·ΔE_k] · [N_μ,total(E_k,θ)/N_k] / ΔE_μ`
   where N_μ,total is the **total number of muons (all directions)** per primary; Φ_p is already "per sr",
   so **do NOT divide again by the muon angular-window solid angle**. Previously I divided by ΔΩ (0°=0.0468, 75°=1.058)
   and also filtered muons by a θ window, overestimating the result by ~8–12× (the erroneous 0.14 primary spectrum happened to cancel it).
   After the fix (Papini spectrum, protons only) 0°@100GeV=1.24e-7 (0.53×Gaisser),
   75°@100GeV=2.19e-7 (0.76×Jokisch); deficit = protons only (missing He/heavy nuclei ~20–30%) + low-energy EMU cutoff.
7. **Primary spectrum = Papini/Grimani/Stephens (same as CRY, citable)**:
   `J_p(E)=3.2009e9·(E[MeV]+920)^-4·E^1.25` [/(MeV·s·m²·sr)], solar minimum;
   high-energy end = `18000·E^-2.75` [m⁻² s⁻¹ sr⁻¹ (GeV/nuc)⁻¹]. At 100 GeV it gives 5.85e-6, consistent with AMS-02.

## Current limitations and next steps

- **run1 is protons only**: missing He/CNO/MgSi/Fe, absolute flux low by ~20% (protons are ~80% of primaries).
- **Primary spectrum is a simple power law**: solar modulation not included at low energies (<10 GeV).
- Next steps:
  1. Add the full composition (5 groups, Hörandel/Poly-gonato), run each group separately and sum with weights.
  2. Overlay the Gaisser/Tang, Bugaev/Reyna analytical models + digitized Figure 2 experimental red points.
  3. Statistics can be scaled up as needed (currently ~10%/bin; reaching 5% only needs ×4 showers).
