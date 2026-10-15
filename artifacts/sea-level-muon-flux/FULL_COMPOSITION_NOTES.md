# Full composition plan and references

## Primary spectrum reference

- **Papini, Grimani & Stephens**, "An estimate of the secondary-proton spectrum
  at small atmospheric depths", *Il Nuovo Cimento C*, Vol. 19, N. 3 (1996).
  (Workspace copy of the paper PDF: `papini_flux.pdf`, the Papini paper PDF)
- Paper Eq. (8): `J(E) = A·(E+B)^-α · E^β`, units particles/(m² sr s GeV/nuc),
  E = kinetic energy per nucleon (GeV/nuc). Parameters in Table II (solar minimum):

| Component | A | B (GeV/nuc) | α | β |
|---|---|---|---|---|
| proton p | 18000 | 0.92 | 4 | 1.25 |
| He | 850 | 0.76 | 3.52 | 0.77 |
| C+O | 62 | 1.05 | 3.25 | 0.5 |

## Full-composition treatment (paper §3)

- "the spectrum of all nuclei with Z > 2 is equivalent to **2.25** times the (C+O) spectrum"
- "in order to obtain a helium spectrum which represents all heavier nuclei of Z > 1
  at the top of the atmosphere, the equivalent C+O spectrum was further multiplied by
  **3.5** and added to the observed primary helium spectrum"

i.e. the primary cosmic rays are represented by only two components:
1. **Protons**: `J_p(E)` (PRMPAR=14)
2. **Effective helium** (representing all Z>1 nuclei): `J_He(E) + 3.5·J_{C+O}(E)` (PRMPAR=402, ^4He)

## Flux unit conversion

- Papini's `J_c(E)` is "per GeV/nuc (kinetic energy)", E = kinetic energy per nucleon.
- CORSIKA `ERANGE` is "total energy per nucleus". For a nucleus of mass number A:
  - kinetic energy per nucleon `E_kin_nuc = E_tot/A − m_nuc` (m_nuc≈0.938 GeV)
  - total-energy-per-nucleus flux `Φ_c(E_tot) = J_c(E_kin_nuc) / A`

## Analysis formula (same as before, summed over the two components)

```
I_μ(E_μ, θ) = Σ_c Σ_k [ Φ_c(E_k)·ΔE_k ] · [ N_μ,c(E_k,θ)/N_k ] / ΔE_μ
             c ∈ {proton, effective helium}
```

## Other references (muon flux standard answers / data)

- Gaisser formula: Gaisser, *Cosmic Rays and Particle Physics*, Cambridge (1990).
- Gaisser/Tang curvature correction: Tang et al. (2006).
- Bugaev/Reyna: Bugaev et al., Phys. Rev. D 58, 054001 (1998); Reyna (2006).
- Smith-Duller/Chatzidakis: Smith & Duller (1959); Chatzidakis et al., NIM A 804, 33 (2015).
- 0° experimental data: L3+C (Achard et al., Phys. Lett. B 598, 15 (2004)).
- 75° experimental data: Jokisch et al., Phys. Rev. D 19, 1368 (1979).
