#!/usr/bin/env bash
# =============================================================================
# NAIO OS — compute-checksums.sh
# Computes sha256 for every non-manifest file in manifest.yaml contents and
# rewrites the manifest in place. manifest.yaml is intentionally self-excluded
# to avoid the impossible self-hash loop.
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
MANIFEST="$ROOT/manifest.yaml"

if [ ! -f "$MANIFEST" ]; then
  echo "manifest.yaml not found at $MANIFEST" >&2
  exit 1
fi

python3 - "$MANIFEST" "$ROOT" <<'PY'
import sys, hashlib
from pathlib import Path
try:
    import yaml
except ImportError as e:
    raise SystemExit("pyyaml is required to compute checksums") from e

manifest_path, root = Path(sys.argv[1]), Path(sys.argv[2])
manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
if not isinstance(manifest, dict):
    raise SystemExit("manifest.yaml must parse to an object")

for item in manifest.get("contents", []):
    rel = item.get("path")
    if not rel:
        continue
    if item.get("self_checksum_excluded") or rel == "manifest.yaml":
        item.pop("sha256", None)
        item["self_checksum_excluded"] = True
        continue
    p = root / rel
    if not p.is_file():
        raise SystemExit(f"missing manifest content: {rel}")
    item["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()

manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=1000), encoding="utf-8")
print(f"✅ checksums written into {manifest_path.name} (manifest self-checksum excluded)")
PY
