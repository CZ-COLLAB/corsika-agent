#!/bin/bash
# Parallel batch runner for the muon flux production.
# Each job: run CORSIKA < card, then convert DAT -> ROOT with CorsikaPlottermini.
# Reads jobs.txt, runs up to NCPU jobs concurrently.
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CORSIKA_ROOT="${CORSIKA_ROOT:-$HOME/corsika-78010}"
MODEL="${1:-sibyll}"
if [ "$MODEL" = "qgs" ]; then
  CORSIKA_BIN="$CORSIKA_ROOT/run/corsika78010Linux_QGSIII_urqmd"
  SUF="_qgs"
else
  CORSIKA_BIN="$CORSIKA_ROOT/run/corsika78010Linux_SIBYLL_urqmd"
  SUF=""
fi
PLOTTER_BIN="$CORSIKA_ROOT/run/CorsikaPlottermini"
RUN_DIR="$CORSIKA_ROOT/run"

NCPU="${NCPU:-18}"
JOBS_FILE="${HERE}/jobs_${MODEL}.txt"
LOGDIR="${HERE}/logs"
mkdir -p "$LOGDIR" "${HERE}/out_0deg${SUF}" "${HERE}/out_75deg${SUF}"

# Build a list of per-job shell command lines (one per line).
# Columns in jobs.txt: theta E runnr seed nshow card outdir
CMD_FILE="$(mktemp)"

while read -r theta E runnr seed nshow card outdir; do
  [[ "$theta" == \#* ]] && continue
  [[ -z "$theta" ]] && continue
  datfile="$outdir/DAT$(printf '%06d' "$runnr")"
  log="$LOGDIR/job_${theta}deg_${runnr}.log"
  # Emit a single command string per job; use markers to keep quoting safe.
  printf '%s\n' \
    "cd \"$RUN_DIR\" && \"$CORSIKA_BIN\" < \"$card\" > \"$log\" 2>&1 && cd \"$outdir\" && \"$PLOTTER_BIN\" \"$datfile\" >> \"$log\" 2>&1" \
    >> "$CMD_FILE"
done < "$JOBS_FILE"

echo "Launching $(wc -l < "$CMD_FILE") jobs with $NCPU parallel workers..."

# Run jobs in parallel, preserving per-job output in logs.
cat "$CMD_FILE" | xargs -P "$NCPU" -I @ bash -c @

rm -f "$CMD_FILE"
echo "Done. Logs in $LOGDIR"
