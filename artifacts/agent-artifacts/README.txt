CorsikaAgent simulation artifacts
=================================

Supporting material for the paper
"From Earth to Mars and Beyond: AI-Driven Cosmic-Ray Flux Prediction
with CorsikaAgent".

This archive collects the simulation inputs and analysis code that were
retained for the runs reported in the paper (steering cards, atmosphere
parameters, build configuration, sample logs, and analysis scripts), as
stated in the text: the workflow "keeps every steering card, executable,
seed, log, and analysis script bound to the result it produced".

Large binary outputs (DAT files, ROOT files, particle stacks) are excluded
because of their size; they are available from the authors on request.

Contents
--------

earth/
  cards/                105 CORSIKA steering cards for the sea-level
                        production: proton primaries, zenith angles 0 deg and
                        75 deg, high-energy model SIBYLL 2.3e or QGSJET-III,
                        low-energy model UrQMD 1.3.1, ECUTS 0.3 0.3 0.003
                        0.003, OBSLEV 0, MAGNET 20.40 43.23, 21 primary
                        energies from 10 GeV to 1e5 GeV (five per decade).
  scripts/              Job generation and analysis scripts (gen_jobs.py,
                        analyze_flux.py, plot_final.py, plot_ratio.py,
                        compile_experimental_data.py, and the enlarged-font
                        plotting variants).
  experimental_data/    Experimental fluxes used for comparison (L3+C
                        vertical, Jokisch 75 deg, BESS-TeV).
  results/              Final flux tables and comparison figures (CSV, PDF).
  logs/                 Sample run logs (smoke tests and one production
                        log).

mars/
  Mars.inp              CORSIKA steering card for the Martian atmosphere run
                        (100 TeV protons, 60 deg zenith, OBSLEV 0).
  Earth.inp             Reference Earth run with the same configuration.
  Earth_prod.inp        Earth production variant.
  MARS_MODIFICATIONS.log
                        Source modifications of the CORSIKA 7.8010 tree used
                        for Mars: five-layer NASA Mars atmosphere (total
                        column about 18.8 g/cm2) and planetary radius
                        3389.5 km.
  overlay_2x2.py        Lateral and longitudinal comparison figure
                        (Fig. 5 of the paper); plot_muons_2x2.py and
                        analyze_corsika.py are the underlying analysis code.
  digitized/            Digitized reference curves from the CORSIKA 8 study
                        (ICRC 2021), lateral and longitudinal, Mars and
                        Earth.

venus/
  Venus_surf_3k.inp     CORSIKA steering card for the Venus surface run
                        (100 TeV protons, 60 deg zenith, OBSLEV 0,
                        MAGNET 0.01 0.01, HILOW 63.1).
  Venus_surf.inp        Larger surface sample configuration.
  test_venus_surf.inp   Smoke-test card for the Venus surface
                        configuration.
  test_venus_urqmd.inp  Smoke-test card for the UrQMD coupling.
  build_venus_atmosphere.py
                        Converts the VIRA temperature profile (Seiff 1985)
                        and the NSSDCA Venus Fact Sheet surface conditions
                        into the five-layer CORSIKA atmosphere model:
                        hydrostatic integration gives the column-depth
                        profile t(h), which is then fitted by four
                        exponential layers and one linear top layer
                        t(h) = A + B exp(-h/C).
  venus_card_values.txt Resulting ATMA, ATMB, ATMC, ATMLAY card values.
  venus_atmosphere.txt  Height, pressure, temperature, density and column
                        depth of the fitted atmosphere.
  plot_2x3_mars_earth_venus.py
                        Three-planet comparison figures.
  plot_venus_surface_2x2.py
                        Venus surface lateral/longitudinal figure.

thunderstorm/
  plot_fig4_compare.py  Regenerates the thunderstorm benchmark figure
                        (Fig. 7 of the paper) from fig4_spectra.npz and the
                        digitized Telescope Array spectra.
  parse_spectra.py      Parses the digitized spectra.
  parse_spectra_50k.py  Parser variant assuming 5e4 reference showers.
  parse_fig4.py         Parser for the original figure.
  fig4_spectra.npz      Binned photon, electron and muon spectra for the
                        three electric-field configurations.
  digitized/            Digitized Telescope Array spectra (gamma, e+-,
                        mu+- at E = 0, +2000, -2000 V/cm).

agent/
  prompts/              The four domain prompts used by CorsikaAgent:
                        SKILL.md (workflow), usage-guide.md (steering-card
                        reference), code-architecture.md (source map),
                        planetary-migration.md (procedure to migrate the
                        simulation to other planets, with the Mars and
                        Venus parameters and sources).

build/
  config.h              Compile-time configuration of the CORSIKA binary
                        used for the production runs.
  BUILD_NOTES.md        Build options and model versions (SIBYLL 2.3e,
                        QGSJET-III, UrQMD 1.3.1; __CURVED__; no external
                        atmosphere).

Primary spectrum
----------------
All runs weight the simulated primaries with the solar-minimum proton
spectrum of Papini et al. (1996), J_p(E) = 18000 (E + 0.92)^-4 E^1.25
per m2 s sr GeV, integrated over 1-1e5 GeV (F_p = 0.209 cm-2 s-1 sr-1).

Software
--------
CORSIKA 7.8010, with SIBYLL 2.3e or QGSJET-III at high energy and
UrQMD 1.3.1 at low energy. Python 3 with numpy, scipy, matplotlib
(and PyROOT for the .root outputs).

Contact
-------
Zhuo Chen (chenzhuo819@stu.pku.edu.cn)
