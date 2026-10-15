#!/usr/bin/env python3
"""Compile experimental sea-level muon flux data (0.6 GeV/c - 3 TeV/c).

Sources (differential muon intensity dN/(dp dA dOmega dt), per momentum):
  - BESS-TeV : Haino et al., Phys. Lett. B 594 (2004) 35-46.  Vertical (cos>0.98),
               sea level (30 m a.s.l., Tsukuba), mu+ and mu- listed separately,
               momentum 0.576-400 GeV/c.  Units m^-2 s^-1 sr^-1 (GeV/c)^-1.
  - L3+C     : Achard et al., Phys. Lett. B 598 (2004) 15-32.  Vertical
               (0.975<cos<1.0), momentum 20-3000 GeV/c, Table 2.
               (values from the CRY analysis macros, converted to per-momentum).
  - Jokisch  : Jokisch et al., Phys. Rev. D 19 (1979) 1368.  75 deg zenith,
               momentum 1-1000 GeV/c.  (values from the CRY analysis macros).
Output: CSV files in ./experimental_data/
"""
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "experimental_data")
os.makedirs(OUT, exist_ok=True)

# BESS-TeV Table 3: (P_center GeV/c, mu+ flux, mu- flux) in m^-2 s^-1 sr^-1 (GeV/c)^-1
bess = [
(0.599,1.34e1,1.25e1),(0.645,1.33e1,1.22e1),(0.694,1.32e1,1.19e1),(0.748,1.27e1,1.15e1),
(0.806,1.26e1,1.13e1),(0.869,1.23e1,1.08e1),(0.934,1.21e1,1.06e1),(1.01,1.16e1,1.00e1),
(1.08,1.10e1,0.96e1),(1.17,1.07e1,0.91e1),(1.26,1.02e1,0.88e1),(1.36,9.78,8.53),
(1.46,9.38,8.01),(1.57,8.72,7.53),(1.70,8.59,7.22),(1.83,7.85,6.72),(1.97,7.41,6.28),
(2.12,7.03,5.71),(2.28,6.38,5.36),(2.46,6.01,4.92),(2.65,5.45,4.62),(2.86,5.02,4.09),
(3.08,4.62,3.69),(3.32,4.17,3.31),(3.57,3.79,3.06),(3.85,3.37,2.70),(4.14,3.02,2.37),
(4.47,2.74,2.11),(4.81,2.41,1.87),(5.18,2.11,1.66),(5.58,1.87,1.46),(6.01,1.63,1.24),
(6.48,1.44,1.13),(6.98,1.21,0.96),(7.52,1.06,0.83),(8.10,9.11e-1,6.93e-1),
(8.72,8.07e-1,6.08e-1),(9.40,7.06e-1,5.15e-1),(10.1,5.67e-1,4.54e-1),
(10.9,4.90e-1,3.85e-1),(11.8,4.38e-1,3.24e-1),(12.7,3.58e-1,2.74e-1),
(13.6,3.07e-1,2.31e-1),(14.7,2.49e-1,1.97e-1),(15.8,2.13e-1,1.68e-1),
(17.1,1.76e-1,1.40e-1),(18.4,1.49e-1,1.15e-1),(19.8,1.22e-1,0.96e-1),
(22.1,9.57e-2,7.36e-2),(25.6,6.69e-2,5.04e-2),(29.7,4.52e-2,3.48e-2),
(34.5,2.93e-2,2.26e-2),(40.1,2.01e-2,1.55e-2),(46.5,1.31e-2,1.04e-2),
(54.0,8.76e-3,6.91e-3),(62.7,5.72e-3,4.54e-3),(72.8,4.01e-3,2.88e-3),
(84.4,2.55e-3,1.93e-3),(98.0,1.55e-3,1.17e-3),(118,9.43e-4,6.95e-4),
(147,4.26e-4,3.65e-4),(184,2.51e-4,1.47e-4),(229,1.18e-4,0.75e-4),
(286,5.58e-5,4.13e-5),(359,2.56e-5,2.45e-5)]

# L3+C (Achard 2004) vertical: (p GeV/c, intensity cm^-2 s^-1 sr^-1 (GeV/c)^-1)
l3c = [
(23.18,1.742286e-05),(30.47,8.165723e-06),(38.02,4.439699e-06),(45.78,2.626474e-06),
(54.04,1.628498e-06),(63.25,1.031476e-06),(74.63,6.399430e-07),(90.13,3.578435e-07),
(114.50,1.758683e-07),(161.30,5.957128e-08),(243.00,1.623817e-08),(381.90,3.644576e-09),
(687.20,4.652940e-10),(1599.00,2.128011e-11)]

# Jokisch 1979 75deg: (p GeV/c, intensity cm^-2 s^-1 sr^-1 (GeV/c)^-1)
jokisch = [
(1.12,2.973e-5),(1.41,3.111e-5),(1.76,3.263e-5),(2.29,3.168e-5),(2.85,3.068e-5),
(3.57,2.848e-5),(4.49,2.606e-5),(5.66,2.332e-5),(7.12,2.021e-5),(8.95,1.705e-5),
(11.26,1.373e-5),(14.17,1.070e-5),(17.83,8.029e-6),(22.44,5.708e-6),(28.23,3.964e-6),
(35.52,2.637e-6),(44.70,1.712e-6),(56.25,1.064e-6),(70.79,6.479e-7),(89.09,3.751e-7),
(112.13,2.208e-7),(141.12,1.234e-7),(177.62,6.632e-8),(223.56,3.735e-8),(281.39,1.869e-8),
(354.18,9.689e-9),(445.81,5.436e-9),(625.46,1.770e-9),(990.22,3.982e-10)]

def write_csv(name, rows):
    with open(os.path.join(OUT, name), "w") as f:
        f.write("p_GeVc  I_cm2_s_sr_perGeVc\n")
        for p, I in rows:
            f.write(f"{p:.6g}\t{I:.6e}\n")

# BESS-TeV: total muon flux = mu+ + mu-, convert m^-2 -> cm^-2 (x1e-4)
bess_tot = [(p, (Ip + Im) * 1e-4) for p, Ip, Im in bess]
write_csv("bess_tev_vertical.csv", bess_tot)
write_csv("l3c_vertical.csv", l3c)
write_csv("jokisch_75deg.csv", jokisch)

# combined (with source tag)
with open(os.path.join(OUT, "muon_flux_experimental_combined.csv"), "w") as f:
    f.write("source  p_GeVc  I_cm2_s_sr_perGeVc\n")
    for p, I in bess_tot: f.write(f"BESS-TeV(2004,0deg)\t{p:.6g}\t{I:.6e}\n")
    for p, I in l3c:      f.write(f"L3+C(2004,0deg)\t{p:.6g}\t{I:.6e}\n")
    for p, I in jokisch:  f.write(f"Jokisch(1979,75deg)\t{p:.6g}\t{I:.6e}\n")

print("wrote to", OUT)
print("  bess_tev_vertical.csv : %d points (0.6-359 GeV/c, mu+ + mu-)" % len(bess_tot))
print("  l3c_vertical.csv      : %d points (23-1600 GeV/c)" % len(l3c))
print("  jokisch_75deg.csv     : %d points (1-990 GeV/c)" % len(jokisch))
