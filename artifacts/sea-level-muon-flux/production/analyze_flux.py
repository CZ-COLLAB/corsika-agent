#!/usr/bin/env python3
"""
Build the sea-level differential muon flux from the production ROOT files.

Correct normalization (per unit perpendicular area, per unit solid angle):
    I_mu(E_mu, theta) = sum_k [ Phi_p(E_k) * dE_k ] * [ N_mu(E_k, theta) / N_k ]
                        / dE_mu
where
    Phi_p = Papini/Grimani/Stephens primary proton spectrum,
    dE_k  = E_k * dlnE_k  (log-grid energy-bin width),
    N_mu  = TOTAL muons at sea level (all directions) per primary,
    N_k   = number of showers at primary energy E_k.

The specific intensity is per unit solid angle through Phi_p (per sr); the
muon yield is the TOTAL number per primary, so NO division by the muon
angular-bin solid angle is needed.  (Earlier versions wrongly divided by the
angular-window solid angle and applied a 1/cos^2(theta) factor; both are
removed here.)

Run1: protons only (Papini), theta = 0 and 75 deg.
"""
import os, glob
import numpy as np
import ROOT
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))

MUON_MASS = 0.105658  # GeV

# Papini / Grimani / Stephens primary proton spectrum (solar minimum),
# converted to cm^-2 s^-1 sr^-1 GeV^-1 with E in GeV:
#   J(E) = 3.2009e9 (E[MeV] + 920)^-4 E[MeV]^1.25   [/(MeV s m^2 sr)]
def phi_p(E):
    Em = 1000.0 * E
    return 3.2009e8 * (Em + 920.0)**-4.0 * Em**1.25

# muon kinetic-energy bins (GeV), log-spaced
EK_MIN, EK_MAX, BINS_PER_DEC = 0.3, 3e3, 8
ndec = np.log10(EK_MAX / EK_MIN)
nbins = int(round(ndec * BINS_PER_DEC))
ek_edges = np.logspace(np.log10(EK_MIN), np.log10(EK_MAX), nbins + 1)


def read_file(path):
    """Return (Eprim, nshow, ek_array) for all muons (all directions)."""
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        return None
    evt = f.Get("Event")
    if not evt:
        f.Close(); return None
    Eprim = np.zeros(1)
    evt.SetBranchAddress("Eprim", Eprim)
    evt.GetEntry(0)
    nshow = evt.GetEntries()
    ek_list = []
    for key in f.GetListOfKeys():
        if key.GetName() != "data_1":
            continue
        nt = f.Get("data_1;%d" % key.GetCycle())
        if not nt:
            continue
        id_v = np.zeros(1); ek_v = np.zeros(1)
        nt.SetBranchAddress("id", id_v)
        nt.SetBranchAddress("ek", ek_v)
        n = nt.GetEntries()
        for i in range(n):
            nt.GetEntry(i)
            if id_v[0] != 5 and id_v[0] != 6:
                continue
            if ek_v[0] > 0:
                ek_list.append(ek_v[0])
    f.Close()
    return float(Eprim[0]), int(nshow), np.array(ek_list)


def collect(theta):
    outdir = os.path.join(HERE, "out_%ddeg" % theta)
    files = sorted(glob.glob(os.path.join(outdir, "DAT*.root")))
    Ek, Nk, Nmu_binned = [], [], []
    for path in files:
        r = read_file(path)
        if r is None:
            continue
        Eprim, nshow, ek = r
        if nshow <= 0:
            continue
        hist, _ = np.histogram(ek, bins=ek_edges)
        Ek.append(Eprim); Nk.append(nshow)
        Nmu_binned.append(hist.astype(float))
    Ek = np.array(Ek); Nk = np.array(Nk)
    Nmu_binned = np.array(Nmu_binned)
    return Ek, Nk, Nmu_binned


def compute_flux(theta):
    Ek, Nk, Nmu_binned = collect(theta)
    order = np.argsort(Ek)
    Ek = Ek[order]; Nk = Nk[order]; Nmu_binned = Nmu_binned[order]

    lnE = np.log(Ek)
    dlnE = np.zeros_like(Ek)
    dlnE[0] = (lnE[1]-lnE[0])/2
    dlnE[-1] = (lnE[-1]-lnE[-2])/2
    dlnE[1:-1] = (lnE[2:]-lnE[:-2])/2

    w = Ek * phi_p(Ek) * dlnE          # Phi_p * dE_k  [cm^-2 s^-1 sr^-1]

    de = np.diff(ek_edges)              # muon energy-bin width (GeV)
    Ekc = np.sqrt(ek_edges[:-1]*ek_edges[1:])

    y = Nmu_binned / Nk[:, None]        # muons per primary per bin
    I = (w[:, None] * y).sum(axis=0) / de    # cm^-2 s^-1 sr^-1 GeV^-1
    var = (w[:, None]**2 * Nmu_binned / (Nk[:, None]**2)).sum(axis=0)
    sigma = np.sqrt(var) / de

    return Ekc, I, sigma, Ek, Nk, Nmu_binned


def main():
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)

    for ax, theta in zip(axes, [0, 75]):
        Ekc, I, sigma, Ek, Nk, Nmu_binned = compute_flux(theta)
        m = I > 0
        ax.errorbar(Ekc[m], I[m], yerr=sigma[m], fmt='o', ms=4,
                    color=('blue' if theta == 0 else 'red'),
                    label="CORSIKA (SIBYLL 2.3e+URQMD, p)")
        ax.set_xscale('log'); ax.set_yscale('log')
        ax.set_xlabel(r"$\mu$ kinetic energy  $E_\mu$ (GeV)")
        if theta == 0:
            ax.set_ylabel(r"$dN/(dE\,dA\,d\Omega\,dt)$  (cm$^{-2}$ s$^{-1}$ sr$^{-1}$ GeV$^{-1}$)")
        ax.set_title(r"$\theta$ = %d$^\circ$" % theta)
        ax.set_xlim(0.3, 3e3)
        ax.set_ylim(1e-13, 1e-1)
        out = np.column_stack([Ekc, I, sigma])
        np.savetxt(os.path.join(HERE, "results", "flux_%ddeg.csv" % theta),
                   out, header="E_kin_GeV  I_cm2_s_sr_GeV  sigma", fmt="%.6e")

    axes[0].legend(fontsize=8)
    plt.tight_layout()
    png = os.path.join(HERE, "results", "flux_0_75deg.pdf")
    plt.savefig(png, dpi=130)
    print("saved", png)
    for theta in [0, 75]:
        Ekc, I, sigma, Ek, Nk, Nmu_binned = compute_flux(theta)
        m = I > 0
        print(f"theta={theta}: {np.sum(m)} non-empty bins, "
              f"flux range [{I[m].min():.2e}, {I[m].max():.2e}]")


if __name__ == "__main__":
    main()
