# Statistics estimate (muon differential flux, 0° / 75°)

## Goal

Reproduce fenrg-09-750159 Figure 2: x-axis muon kinetic energy 1–1000 GeV (log bins),
y-axis I_μ(E_μ) = dN/(dE dA dΩ dt). Require controllable per-bin statistical error
for each curve.

## Error sources and criteria

The flux of each log bin is a sum over "primary grid + primary-spectrum weighting".
The bin relative error ≈ 1/√(N_μ,bin), the accumulated muon count in that bin
(Poisson; still of this order after the weighted-variance correction):

- 10% error → ~100 μ/bin needed
- 5% error → ~400 μ/bin needed
- 2% error → ~2500 μ/bin needed

For reproducing Figure 2 (the models themselves differ by 10–50%), 5–10% suffices;
for a pretty curve use 5%.

## Key physics arguments (determine how the statistics are allocated)

1. Muons reaching sea level at angle θ come mainly from primaries with
   E_p ≈ 10–20 × E_μ.
   → 1 GeV muons ← ~10–20 GeV primaries; 1 TeV muons ← ~10–30 TeV primaries.
   → So covering muons up to 1 TeV requires primaries only up to ~100 TeV;
   **1 PeV and THIN are NOT needed**.
2. The primary spectrum Φ_p ∝ E^−2.7 is steep → the low-energy muon flux is
   dominated by low-energy primaries, and the high-energy muon flux is dominated
   by "the lowest-energy primary that can still produce it".
3. A single high-energy primary shower produces very many muons (see table below),
   so at the high-energy end **each point needs only a few showers**; a low-energy
   primary produces only a fraction of a muon per shower, so the low-energy end
   **needs thousands of showers** (but each is cheap).

## Muon yield model (for the estimate)

From existing scan data (0°, EMU=0.3, single showers): 100 GeV→2, 1e3→6, 1e4→139,
1e5→1024, 1e6→12480. Fit n_μ(E_p) ≈ 0.025·E_p^0.95 (GeV).
Smoke-test cross-check (10 TeV protons): model 0.025·10^3.8≈158, measured 169, consistent.
**URQMD forces EHAD≥0.3**, so EMU=0.3 is kept: **n_μ(E_p) ≈ 0.025·E_p^0.95**
(total muons >0.3 GeV per shower). The muon spectrum is approximately spread
uniformly in log-energy from ~0.3 GeV to 0.1·E_p.

Invert this model to get the number of showers needed per bin (see below).

## Recommended statistics (protons, per zenith angle, 5 bins/decade)

### Plan A — sufficient (~10%/bin, enough to reproduce Figure 2)

| E_p decade (GeV) | points | showers/point | total showers | single-core CPU estimate |
|---|---|---|---|---|
| 1e1–1e2 | 5 | 2000 | 10,000 | ~0.3 h |
| 1e2–1e3 | 5 | 300 | 1,500 | ~0.4 h |
| 1e3–1e4 | 5 | 60 | 300 | ~0.8 h |
| 1e4–1e5 | 5 | 12 | 60 | ~1.2 h |
| 1e5–1e6 | 5 | 2 | 10 | ~1 h |
| **Total** | | | **~11,900** | **~4 h/angle** |

### Plan B — fine (~5%/bin, smoother figure)

| E_p decade (GeV) | showers/point | total showers | single-core CPU |
|---|---|---|---|
| 1e1–1e2 | 5000 | 25,000 | ~0.7 h |
| 1e2–1e3 | 800 | 4,000 | ~1 h |
| 1e3–1e4 | 150 | 750 | ~2 h |
| 1e4–1e5 | 30 | 150 | ~2.5 h |
| 1e5–1e6 | 5 | 25 | ~2.5 h |
| **Total** | | **~29,900** | **~9 h/angle** |

## Multiplicative corrections

- **75° vs 0°**: slant depth ~4000 vs 1033 g/cm², muon yield lower by ~5× (existing
  data: 139→22 at 1e4 GeV, 1024→211 at 1e5 GeV). Moreover 75° has a minimum
  reachable muon energy (~a few GeV), so the lowest few bins have no data anyway.
  → use **2–3×** the 0° shower count at 75° for comparable precision
  (about 2–3× the 0° cost).
- **Full composition (p/He/CNO/MgSi/Fe)**: heavy nuclei produce more muons per
  shower with smaller spectral weight, so each group needs fewer showers than the
  proton case. Full-composition total cost ≈ proton cost × **2.5–3**.

## Total budget

| Configuration | 0° | 75° | total (single core) |
|---|---|---|---|
| protons, plan A | ~4 h | ~10 h | ~14 h |
| protons, plan B | ~9 h | ~22 h | ~31 h |
| full composition, plan B | ~25 h | ~55 h | ~80 h |

- Single-core totals range from ~14 h (proton sufficient version) to ~80 h
  (full-composition fine version).
- **HTCondor batches strongly recommended** (see the `~/corsika_job/` template):
  split into thousands of independent tasks by (θ, component, E_p), each task with
  tens to thousands of NSHOW and independent seeds — naturally parallel, wall-clock
  time can be compressed to a few hours.
- Suggested order: run the **smoke test** first (1 shower @ 1e4 GeV for each of
  0°/75°, ECUTS=0.05), confirm low-energy muons really appear and the θ windows
  are correct, then validate the workflow with a small plan-A batch, and finally
  scale up to plan B full composition.

## Seeds and independence

Each shower uses a progressive first SEED parameter (e.g. SEED = base + k) to
guarantee independence. Different (θ, component, E_p) tasks use different seed
blocks to avoid correlations.
