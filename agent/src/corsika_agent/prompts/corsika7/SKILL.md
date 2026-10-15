---
name: corsika7
description: Use, inspect, and extend the installed CORSIKA 7.8010 runtime, steering cards, DAT output, and legacy Fortran architecture.
compatibility: opencode
metadata:
  simulator: corsika-7
  release: "7.8010"
---

# CORSIKA 7.8010

Use this skill whenever the task explicitly uses CORSIKA 7, its steering cards, its DAT output,
or its legacy Fortran source architecture.

## Read only what the task needs

- For configuring, running, debugging, or analysing CORSIKA 7, first read
  `references/usage-guide.md` completely.
- For source navigation, new options, output changes, physics-process changes, or architecture
  questions, also read `references/code-architecture.md` completely.
- For simulations on other planets (non-Earth atmospheres: Mars, Venus, etc.),
  read `references/planetary-migration.md` completely. It documents how to
  migrate CORSIKA 7 to another planet via `ATMOD 0` + `ATMA/ATMB/ATMC/ATMLAY`
  cards, covering ALL parameters (atmosphere, magnetic field, gravity, radius,
  composition, temperature profile, observation level, primary spectrum), with
  authoritative (NSSDCA/NASA) parameters, sources, and the known hardcoded
  5th-layer constraint.
- The references are expert-prepared summaries, not an oracle. Check uncertain details against
  the installed executable, `include/config.h`, runtime logs, sample cards, and official material
  available in the workspace. If the summary and the actual build differ, the actual build wins.

## Installed interface

The installed executable is one concrete compiled option/model combination. A steering card
cannot enable a compile-time feature absent from that binary. Inspect the build configuration
instead of guessing.

A missing compile-time feature is not a blocker: modify the source under `src/` (e.g. atmosphere
parameters in the DATA statements, new cards in `DATAC`, output logic, physics options) and
rebuild with `make`. This is a normal workflow for this agent, not a last resort. Run a smoke
test after rebuilding before scaling up. Explain a blocker only after checking the installed
source/build artifacts and the available development path.

Keep chat concise. Put cards, code, commands, logs, parsed data, and plots in files. In the final
answer, state what actually ran, what was changed, where the outputs are, and any material physics
approximation.
