#!/usr/bin/env bash
# Rebuild assets/governance-kit.zip from governance-kit/.
#
# On 11 August 2026 the downloadable kit was found shipping a CHARTER.md that
# predated a rails rewrite — every nurse who downloaded it got the old rules.
# Nothing regenerated it, so nothing caught it. This is that missing step.
#
# Run it after ANY edit to governance-kit/. Verify prints what changed.
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
SRC="$ROOT/governance-kit"
OUT="$ROOT/assets/governance-kit.zip"

[ -d "$SRC" ] || { echo "✗ no governance-kit/ at $SRC"; exit 1; }
command -v zip >/dev/null || { echo "✗ 'zip' not installed"; exit 1; }

# Refuse to ship a kit whose boundaries drifted from the doctrine.
DOCTRINE="$ROOT/naio-os/DOCTRINE.md"
if [ -f "$DOCTRINE" ] && ! grep -q "tool has no clearance" "$SRC/CHARTER.md" 2>/dev/null; then
  echo "✗ CHARTER.md does not carry the tool-not-scope wording from Rail 2."
  echo "  Refusing to build a kit that contradicts the doctrine it ships with."
  exit 2
fi

mkdir -p "$(dirname "$OUT")"
rm -f "$OUT"
( cd "$SRC" && zip -qr "$OUT" . -x '.*' -x '__MACOSX/*' )

echo "✓ rebuilt $OUT"
unzip -l "$OUT" | tail -n +4 | head -n -2 | awk '{printf "    %s\n", $4}'
echo
echo "  CHARTER.md rail check: $(unzip -p "$OUT" CHARTER.md | grep -c 'tool has no clearance') match(es)"
echo "  Agents propose. Humans judge. Nurses steward."
