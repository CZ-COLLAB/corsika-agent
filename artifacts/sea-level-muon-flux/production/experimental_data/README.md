# Sea-level muon differential flux experimental data

All data are differential intensities `I = dN/(dp dA dΩ dt)`, units cm⁻² s⁻¹ sr⁻¹ (GeV/c)⁻¹,
x-axis momentum p (GeV/c).

## Sources and references

1. **BESS-TeV (vertical, 0.6–400 GeV/c)**
   - Haino et al., "Measurements of Primary and Atmospheric Cosmic-Ray Spectra
     with the BESS-TeV Spectrometer", *Phys. Lett. B* 594 (2004) 35–46.
   - arXiv: astro-ph/0403704; doi:10.1016/j.physletb.2004.05.019
   - Data: Table 3 of the paper (μ⁺ and μ⁻ listed separately, merged into μ⁺+μ⁻
     and converted from m⁻² to cm⁻²).
   - Conditions: sea level (30 m a.s.l., Tsukuba), near vertical (cosθ>0.98).

2. **L3+C (vertical, 20–3000 GeV/c)**
   - Achard et al. (L3 Collaboration), "Measurement of the atmospheric muon
     spectrum from 20 to 3000 GeV", *Phys. Lett. B* 598 (2004) 15–32.
   - doi:10.1016/j.physletb.2004.08.003
   - Data: Table 2 of the paper (most vertical bin, 0.975<cosθ<1.0), converted
     from Φ·p³ to dN/dp (values consistent with the L3+C data in the cry_v1.7
     analysis macro).

3. **Jokisch (75°, 1–1000 GeV/c)**
   - Jokisch, Carstensen, Dau, Meyer, Allkofer, "Cosmic-ray muon spectrum up to
     1 TeV at 75° zenith angle", *Phys. Rev. D* 19 (1979) 1368–1372.
   - doi:10.1103/PhysRevD.19.1368
   - Data: consistent with the Jokisch data in the cry_v1.7 analysis macro.

## Notes

- Below 0.1 GeV/c there is essentially no reliable differential flux data (muons
  near their rest mass, severe decay, very hard to measure); the practical lower
  limit is BESS-TeV's 0.576 GeV/c.
- The three datasets differ slightly in zenith angle/altitude (BESS-TeV and L3+C
  vertical; Jokisch at 75°); please note this when citing.

## Files

- bess_tev_vertical.csv — vertical, 65 points, 0.6–359 GeV/c (μ⁺+μ⁻)
- l3c_vertical.csv — vertical, 14 points, 23–1600 GeV/c
- jokisch_75deg.csv — 75°, 29 points, 1–990 GeV/c
- muon_flux_experimental_combined.csv — combined (with source labels)
