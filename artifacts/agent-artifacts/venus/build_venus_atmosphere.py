#!/usr/bin/env python3
"""Build Venus atmosphere column-depth profile t(h) from VIRA-style T(h),
then fit CORSIKA 7 5-layer model (4 exponential + fixed linear top layer)
and emit ATMA/ATMB/ATMC/ATMLAY card values.

Sources (to be cross-checked before publication):
  - NSSDCA Venus Fact Sheet (surface P=92 bar, T=737 K, g=8.87 m/s^2,
    mean mol. mass 43.45 g/mol, scale height 15.9 km)
  - VIRA: Seiff et al. 1985, Adv. Space Res. 5(11), 3-58
  - Globus+ 2021 (arXiv:2101.00530) uses VeGa-2 probe profile (Linkin 1986)
"""
import os
import numpy as np
from scipy.optimize import curve_fit

# ---- Venus physical constants (NSSDCA) ----
g = 8.87            # m/s^2 surface gravity
Mmol = 43.45e-3     # kg/mol mean molecular weight (96.5% CO2 + 3.5% N2)
Rgas = 8.314462618  # J/(mol K)
P0 = 9.2e6          # Pa surface pressure (92 bar)
R_venus = 6051.8e3  # m

# ---- VIRA temperature profile (piecewise linear knots) ----
# h (km) -> T (K). Approximate VIRA mean profile; cross-check Seiff 1985.
T_knots_km = np.array([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55,
                       60, 65, 70, 75, 80, 85, 90, 95, 100, 110, 120.0])
T_knots_K = np.array([735, 695, 655, 615, 575, 535, 495, 455, 415, 375, 350, 310,
                      260, 245, 230, 215, 200, 190, 180, 175, 170, 175, 250.0])

def T_of_h(h_m):
    return np.interp(h_m, T_knots_km, T_knots_K)

# ---- integrate hydrostatic equilibrium to get P(h), t(h) ----
# dP/dh = -rho g, rho = P Mmol / (R T)
# t(h) [g/cm^2] = P(h)/g * 0.1   (P in Pa -> kg/m^2 -> *0.1 g/cm^2)
h_km = np.linspace(0, 130, 1301)
dh = h_km[1] - h_km[0]  # km
T = T_of_h(h_km)
# d ln P / dh = - Mmol g / (R T) ; integrate from surface (P0) upward
# per km: - Mmol g / (R T) * 1000
dlnP = - Mmol * g / (Rgas * T) * 1000.0  # per km
lnP = np.zeros_like(h_km)
lnP[0] = np.log(P0)
# integrate lnP = lnP0 + integral_0^h dlnP dh' via trapezoid
for i in range(1, len(h_km)):
    lnP[i] = lnP[i - 1] + 0.5 * (dlnP[i - 1] + dlnP[i]) * dh
P = np.exp(lnP)
t = P / g * 0.1  # g/cm^2

print("surface t(0) = %.4e g/cm^2 (target ~1.037e5)" % t[0])
print("1 bar (P=1e5 Pa) occurs at h=%.1f km, t=%.1f g/cm^2" %
      (h_km[np.argmin(np.abs(P - 1e5))], t[np.argmin(np.abs(P - 1e5))]))
print("50 km: P=%.2f bar, t=%.1f g/cm^2" % (P[500] / 1e5, t[500]))
print("100 km: P=%.4e bar, t=%.4f g/cm^2" % (P[1000] / 1e5, t[1000]))

# save profile for reference
np.savetxt(os.path.expanduser('~/corsika_Mars/run/venus/venus_atmosphere.txt'),
           np.column_stack([h_km, T, P, t]),
           header='h_km  T_K  P_Pa  t_gcm2')

# ---- CORSIKA 7 model ----
# Layer i (1..4): t(h) = A_i + B_i exp(-h/C_i)  over [H_i, H_{i+1}]
# Layer 5: t(h) = A5 - h/C5  (linear), A5=0.01128292, C5=1e9 FIXED
# HLAY(6) = HEIGH(0) = A5*C5 = 112.8 km (fixed top of atmosphere)
A5 = 0.01128292
C5 = 1.0e9

# choose layer boundaries (cm). Put the observation level (~50 km, ~1 bar
# cloud deck) exactly on a boundary node so its column is captured exactly.
# H = [H1=0, H2, H3, H4, H5, H6] ; H5 -> start of fixed 5th (linear) layer.
H = np.array([0.0, 20.0, 40.0, 50.0, 100.0, 112.8]) * 1e5  # cm (H1..H6)
# H6 = A5*C5 = 112.8 km fixed
print("\nHLAY(6) = %.2f km (fixed)" % (A5 * C5 / 1e5))

# t at each boundary (from VIRA profile). Layer 5 is CORSIKA-fixed linear
# t(h)=A5-h/C5 covering [H5,112.8km]; it only governs the negligible top tail
# (t <~ 0.03 g/cm^2). For exact continuity at H5, force t(H5) = A5 - H5/C5
# (the difference vs VIRA's ~0.026 g/cm^2 is irrelevant for muon physics).
t_b = np.array([np.interp(h / 1e5, h_km, t) for h in H])
t_b[4] = A5 - H[4] / C5  # continuity with fixed layer 5
print("boundary columns t(H) [g/cm^2]:", t_b)

A = np.zeros(5)
B = np.zeros(5)
C = np.zeros(5)
A[4] = A5
C[4] = C5

# Fit layers 1..4: endpoints t(H_i)=t_b[i-1], t(H_{i+1})=t_b[i] are enforced
# exactly (continuity at boundaries). For each layer scan the scale height C_i
# to minimise the RMS relative error vs the VIRA column profile inside the layer.
def ab_from_C(t0, t1, h0, h1, Cs):
    e0 = np.exp(-h0 / Cs)
    e1 = np.exp(-h1 / Cs)
    Bs = (t0 - t1) / (e0 - e1)
    As = t0 - Bs * e0
    return As, Bs

for i in range(4):
    h0 = H[i]
    h1 = H[i + 1]
    t0 = t_b[i]
    t1 = t_b[i + 1]
    # candidate scale heights: local physical scale height +- factor
    hm = (h0 + h1) / 2 / 1e5  # km
    Hs0 = Rgas * T_of_h(hm) / (Mmol * g) * 100.0  # cm (midpoint scale height)
    Cs_candidates = np.logspace(np.log10(Hs0 * 0.3), np.log10(Hs0 * 3.0), 200)
    hs = np.linspace(h0, h1, 100)
    tv = np.interp(hs / 1e5, h_km, t)
    best = None
    for Cs in Cs_candidates:
        As, Bs = ab_from_C(t0, t1, h0, h1, Cs)
        tfit = As + Bs * np.exp(-hs / Cs)
        rms = np.sqrt(np.mean(((tfit - tv) / np.maximum(tv, 1e-9)) ** 2))
        if best is None or rms < best[0]:
            best = (rms, As, Bs, Cs)
    A[i], B[i], C[i] = best[1], best[2], best[3]
    print("layer %d: A=%.6e B=%.6e C=%.6e (H %d-%d km, rel rms=%.3g)" %
          (i + 1, A[i], B[i], C[i], H[i] / 1e5, H[i + 1] / 1e5, best[0]))

# verify monotonic constraint THICKL(L) >= AATM(L-1)
ok = True
for L in range(1, 5):
    if t_b[L] < A[L - 1]:
        ok = False
        print("  !! constraint violated at layer %d: t(H%d)=%.4e < A%d=%.4e" %
              (L + 1, L + 1, t_b[L], L, A[L - 1]))
print("monotonicity constraint:", "OK" if ok else "VIOLATED")

# ---- reconstruct full t(h) from the CORSIKA model and compare to VIRA ----
def corsika_thick(h_cm):
    h = h_cm
    if h < H[1]:
        return A[0] + B[0] * np.exp(-h / C[0])
    elif h < H[2]:
        return A[1] + B[1] * np.exp(-h / C[1])
    elif h < H[3]:
        return A[2] + B[2] * np.exp(-h / C[2])
    elif h < H[4]:
        return A[3] + B[3] * np.exp(-h / C[3])
    else:
        return A[4] - h / C[4]

corsika_thick = np.vectorize(corsika_thick)
hc = np.linspace(0, 112.8e5, 2000)
t_corsika = corsika_thick(hc)
t_vira = np.interp(hc / 1e5, h_km, t)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
ax[0].plot(t_vira, hc / 1e5, label='VIRA (Seiff 1985 / NSSDCA)', lw=2)
ax[0].plot(t_corsika, hc / 1e5, '--', label='CORSIKA 5-layer fit', lw=2)
ax[0].set_xscale('log')
ax[0].set_xlabel('column depth t (g/cm$^2$)')
ax[0].set_ylabel('height (km)')
ax[0].legend(fontsize=9)
ax[0].set_title('Venus atmosphere: column vs height')
rel = np.abs(t_corsika - t_vira) / np.maximum(t_vira, 1e-9)
ax[1].plot(rel, hc / 1e5, lw=1.5)
ax[1].set_xlabel('relative |fit - VIRA| error')
ax[1].set_ylabel('height (km)')
ax[1].set_title('fit error')
ax[1].set_xscale('log')
plt.tight_layout()
plt.savefig(os.path.expanduser('~/corsika_Mars/run/venus/venus_atmosphere_fit.png'), dpi=130)
print("fit plot saved to venus_atmosphere_fit.png")

# ---- emit cards ----
print("\n=== CORSIKA CARD VALUES ===")
print("ATMA    %.8g  %.8g  %.8g  %.8g" % (A[0], A[1], A[2], A[3]))
print("ATMB    %.8g  %.8g  %.8g  %.8g" % (B[0], B[1], B[2], B[3]))
print("ATMC    %.8g  %.8g  %.8g  %.8g" % (C[0], C[1], C[2], C[3]))
print("ATMLAY  %.6g  %.6g  %.6g  %.6g" % (H[1], H[2], H[3], H[4]))

np.savetxt(os.path.expanduser('~/corsika_Mars/run/venus/venus_card_values.txt'),
           np.array([A[0], A[1], A[2], A[3], B[0], B[1], B[2], B[3],
                     C[0], C[1], C[2], C[3], H[1], H[2], H[3], H[4]]),
           header='A1 A2 A3 A4 B1 B2 B3 B4 C1 C2 C3 C4 H2 H3 H4 H5')
print("\ncard values saved to venus_card_values.txt")
