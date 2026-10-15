#!/usr/bin/env bash
# Run CORSIKA (SIBYLL 2.3e + UrQMD) at a fixed zenith angle for the
# Cohu et al. Fig.2 muon-flux-vs-angle reproduction.
# Usage: ./run_one.sh <theta_deg> <runnr> <nshow>
set -euo pipefail

CORSIKA_ROOT="${CORSIKA_ROOT:-$HOME/corsika-78010}"

TH="${1:?theta}"
RUNNR="${2:?runnr}"
NSHOW="${3:?nshow}"

CORSIKA="$CORSIKA_ROOT/run/corsika78010Linux_SIBYLL_urqmd"
RUNDIR="$CORSIKA_ROOT/run"
OUT=out
mkdir -p "$OUT"

INP="$OUT/inp_theta${TH}.inp"
cat > "$INP" <<EOF
RUNNR   ${RUNNR}
EVTNR   1
SEED    $((12345 + RUNNR)) 0 0
SEED    $((67890 + RUNNR)) 0 0
NSHOW   ${NSHOW}
PRMPAR  14
ERANGE  1.E1 1.E7
ESLOPE  -1.7
THETAP  ${TH}. ${TH}.
PHIP    0. 0.
SIBYLL  T 0
SIBSIG  T
URQMD   T 0
ELMFLG  T T
ECUTS   0.3 0.3 0.003 0.003
OBSLEV  0.
MAGNET  22.71 40.96
PAROUT  T T
DIRECT  ${OUT}/
EXIT
EOF

cd "$RUNDIR"
echo "[$(date +%H:%M:%S)] start theta=${TH} run=${RUNNR} nshow=${NSHOW}"
"$CORSIKA" < "$INP" > "$OUT/corsika_theta${TH}.lst" 2>&1
echo "[$(date +%H:%M:%S)] done  theta=${TH} run=${RUNNR}"
