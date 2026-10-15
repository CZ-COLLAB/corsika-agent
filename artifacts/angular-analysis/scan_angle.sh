#!/usr/bin/env bash
# Chunked angular scan. Each chunk runs CHUNK showers, dumps per-event
# (Eprim, N_mu) to events_theta<TH>.txt, then deletes the bulky DAT.
# Usage: ./scan_angle.sh <theta> <runnr_base> <nchunk> <chunk> [emax]
set -euo pipefail

CORSIKA_ROOT="${CORSIKA_ROOT:-$HOME/corsika-78010}"

TH="${1:?theta}"
RUNNR="${2:?runnr}"
NCHUNK="${3:?nchunk}"
CHUNK="${4:?chunk}"
EMAX="${5:-1.E6}"

CORSIKA="$CORSIKA_ROOT/run/corsika78010Linux_SIBYLL_urqmd"
RUNDIR="$CORSIKA_ROOT/run"
OUT=out
EV="$OUT/events_theta${TH}.txt"
mkdir -p "$OUT"
: > "$EV"

cd "$RUNDIR"
for k in $(seq 1 "$NCHUNK"); do
  RN=$((RUNNR * 100 + k))
  S1=$((1000000 + RUNNR * 1000 + k))
  DAT=$(printf 'DAT%06d' "$RN")
  INP="$OUT/inp_theta${TH}_${k}.inp"
  cat > "$INP" <<EOF
RUNNR   ${RN}
EVTNR   1
SEED    ${S1} 0 0
SEED    $((S1 + 7)) 0 0
NSHOW   ${CHUNK}
PRMPAR  14
ERANGE  1.E1 ${EMAX}
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
  "$CORSIKA" < "$INP" > "$OUT/corsika_theta${TH}_${k}.lst" 2>&1
  if [ -f "$OUT/$DAT" ]; then
    python3 "$OUT/../dump_events.py" "$OUT/$DAT" >> "$EV"
    rm -f "$OUT/$DAT" "$OUT/$DAT.tab"
  fi
  echo "[$(date +%H:%M:%S)] theta=${TH} chunk ${k}/${NCHUNK} done ($(wc -l < "$EV") events)"
done
echo "[$(date +%H:%M:%S)] theta=${TH} COMPLETE"
