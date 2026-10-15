#!/bin/bash
# Run the isotropic primary injection production (THETAP 0 89).
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CORSIKA_ROOT="${CORSIKA_ROOT:-$HOME/corsika-78010}"
CORSIKA_BIN="$CORSIKA_ROOT/run/corsika78010Linux_SIBYLL_urqmd"
PLOTTER_BIN="$CORSIKA_ROOT/run/CorsikaPlottermini"
RUN_DIR="$CORSIKA_ROOT/run"
NCPU="${NCPU:-18}"
JOBS_FILE="${HERE}/jobs_iso.txt"
LOGDIR="${HERE}/logs"
OUTDIR="${HERE}/out_iso"
mkdir -p "$LOGDIR" "$OUTDIR"

CMD_FILE="$(mktemp)"
while read -r E runnr seed nshow card; do
  [[ "$E" == \#* ]] && continue
  [[ -z "$E" ]] && continue
  datfile="$OUTDIR/DAT$(printf '%06d' "$runnr")"
  # skip jobs whose root file already exists (resume support)
  [ -f "$datfile.root" ] && continue
  log="$LOGDIR/job_iso_${runnr}.log"
  printf '%s\n' \
    "cd \"$RUN_DIR\" && \"$CORSIKA_BIN\" < \"$card\" > \"$log\" 2>&1 && cd \"$OUTDIR\" && \"$PLOTTER_BIN\" \"$datfile\" >> \"$log\" 2>&1" \
    >> "$CMD_FILE"
done < "$JOBS_FILE"

echo "Launching $(wc -l < "$CMD_FILE") isotropic jobs with $NCPU workers..."
cat "$CMD_FILE" | xargs -P "$NCPU" -I @ bash -c @
rm -f "$CMD_FILE"
echo "Done."
