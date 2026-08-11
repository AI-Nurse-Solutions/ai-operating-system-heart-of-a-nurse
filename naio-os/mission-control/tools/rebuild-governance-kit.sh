#!/usr/bin/env bash
# Rebuild assets/governance-kit.zip from governance-kit/.
#
# On 11 August 2026 the downloadable kit was found shipping a CHARTER.md that
# predated a rails rewrite — every nurse who downloaded it got the old rules.
# Nothing regenerated it, so nothing caught it. This is that missing step.
#
# Run it after ANY edit to governance-kit/. Verify prints what changed.
set -euo pipefail

# tools/ → mission-control/ → naio-os/ → the repo root. Two levels landed on
# naio-os/, where there is no governance-kit/, so the script exited 1 before it
# rebuilt anything unless a caller passed ROOT explicitly.
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
SRC="$ROOT/governance-kit"
OUT="$ROOT/assets/governance-kit.zip"

[ -d "$SRC" ] || { echo "✗ no governance-kit/ at $SRC"; exit 1; }
command -v zip >/dev/null || { echo "✗ 'zip' not installed"; exit 1; }

# Refuse to ship a kit whose boundaries drifted.
#
# This guard used to look for wording ("tool has no clearance") that appears in
# no file in this repository, gated behind `[ -f naio-os/DOCTRINE.md ]` — a path
# that does not exist either. It could therefore never fire: a CHARTER.md with
# its boundaries deleted would have shipped. It now checks the boundary the kit
# actually carries, and fails closed when CHARTER.md is missing.
CHARTER="$SRC/CHARTER.md"
[ -f "$CHARTER" ] || { echo "✗ no CHARTER.md in $SRC — refusing to build a kit with no charter"; exit 2; }
if ! grep -qi "Never handles patient-identifying information" "$CHARTER"; then
  echo "✗ CHARTER.md no longer carries the no-PHI boundary."
  echo "  Refusing to build a kit that contradicts the rules it ships with."
  exit 2
fi

mkdir -p "$(dirname "$OUT")"
rm -f "$OUT"
( cd "$SRC" && zip -qr "$OUT" . -x '.*' -x '__MACOSX/*' )

echo "✓ rebuilt $OUT"
# unzip -Z1, not `head -n -2`: a negative line count is a GNU extension, and BSD
# head (macOS, which this project targets for the Apple Notes bridge) rejects it
# — under `set -o pipefail` that exits non-zero after the zip was already built.
unzip -Z1 "$OUT" | awk '{printf "    %s\n", $0}'
echo
echo "  CHARTER.md boundary check: $(unzip -p "$OUT" CHARTER.md | grep -ci 'Never handles patient-identifying information') match(es)"
echo "  Agents propose. Humans judge. Nurses steward."
