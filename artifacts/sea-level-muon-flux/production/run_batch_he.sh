#!/bin/bash
# Run the He (PRMPAR=402) production.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CORSIKA_ROOT="${CORSIKA_ROOT:-$HOME/corsika-78010}"
CORSIKA_BIN="$CORSIKA_ROOT/run/corsika78010Linux_SIBYLL_urqmd"
PLOTTER_BIN="$CORSIKA_ROOT/run/CorsikaPlottermini"
RUN_DIR="$CORSIKA_ROOT/run"
NCPU="${NCPU:-18}"
JOBS_FILE="${HERE}/jobs_he.txt"
LOGDIR="${HERE}/logs"
mkdir -p "$LOGDIR" "${HERE}/out_0deg_he" "${HERE}/out_75deg_he"

CMD_FILE="$(mktemp)"
while read -r theta E runnr seed nshow card outdir; do
  [[ "$theta" == \#* ]] && continue
  [[ -z "$theta" ]] && continue
  datfile="$outdir/DAT$(printf '%06d' "$runnr")"
  log="$LOGDIR/job_he_${theta}deg_${runnr}.log"
  printf '%s\n' \
    "cd \"$RUN_DIR\" && \"$CORSIKA_BIN\" < \"$card\" > \"$log\" 2>&1 && cd \"$outdir\" && \"$PLOTTER_BIN\" \"$datfile\" >> \"$log\" 2>&1" \
    >> "$CMD_FILE"
done < "$JOBS_FILE"

echo "Launching $(wc -l < "$CMD_FILE") He jobs with $NCPU workers..."
cat "$CMD_FILE" | xargs -P "$NCPU" -I @ bash -c @
rm -f "$CMD_FILE"
echo "Done."
