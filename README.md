# CorsikaAgent

CorsikaAgent is an AI research agent for CORSIKA 7 cosmic-ray air-shower simulations,
together with the reproducibility archive for the paper:

> **From Earth to Mars and Beyond: AI-Driven Cosmic-Ray Flux Prediction with CorsikaAgent**

The repository is organized in two parts:

| Directory | Contents |
|---|---|
| [`agent/`](agent/) | The CorsikaAgent package: an [OpenCode](https://opencode.ai)-based agent whose entire domain knowledge consists of four CORSIKA 7 prompt documents, plus a web chat interface. See [`agent/README.md`](agent/README.md) and [`agent/SETUP.md`](agent/SETUP.md) for deployment. |
| [`artifacts/`](artifacts/) | The simulation artifacts and analysis code behind the paper: sea-level and angular muon-flux studies, planetary-atmosphere runs (Mars, Venus), the thunderstorm benchmark, build evidence, and the agent prompt snapshots used for the runs. See [`artifacts/README.md`](artifacts/README.md). |

Large binary outputs (CORSIKA DAT files, ROOT files, particle stacks) are not
included because of their size; they are available from the authors on request.

## Requirements

- CORSIKA 7.8010 distribution (source tree + compiled `run/` directory)
- Python 3 (numpy, scipy, matplotlib; PyROOT for ROOT outputs)
- [OpenCode](https://opencode.ai) for the agent

The prompt documents and scripts assume the CORSIKA distribution lives at
`~/corsika-78010`; the path is configurable via the `MUON_CORSIKA7_ROOT`
environment variable (agent) or `CORSIKA_ROOT` (analysis scripts).

## Contact

Zhuo Chen — chenzhuo819@stu.pku.edu.cn
