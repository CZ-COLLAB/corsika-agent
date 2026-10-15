# Artifacts

Simulation artifacts and analysis code for the paper
*"From Earth to Mars and Beyond: AI-Driven Cosmic-Ray Flux Prediction with CorsikaAgent"*.

| Directory | Contents |
|---|---|
| [`sea-level-muon-flux/`](sea-level-muon-flux/) | Absolute sea-level muon flux at 0° and 75° zenith (SIBYLL 2.3e and QGSJET-III; proton, helium and isotropic primaries), weighting and statistics notes, comparison with experimental data (L3+C, Jokisch, BESS-TeV). |
| [`angular-analysis/`](angular-analysis/) | Zenith-angle scan (0–90°) of the integral muon flux; per-angle runs, analysis and plotting scripts. |
| [`build-evidence/`](build-evidence/) | Build configuration of the CORSIKA 7.8010 executables used (`config.h`, build notes, interaction-model versions). |
| [`agent-artifacts/`](agent-artifacts/) | Archive of the runs reported in the paper: Earth (sea-level production), Mars, Venus and thunderstorm benchmarks, each with steering cards, analysis scripts and sample logs; plus the four agent prompt snapshots. See [`agent-artifacts/README.txt`](agent-artifacts/README.txt) for a detailed inventory. |

Large binary outputs (DAT/ROOT files, particle stacks) are not stored here; they are
available from the authors on request.
