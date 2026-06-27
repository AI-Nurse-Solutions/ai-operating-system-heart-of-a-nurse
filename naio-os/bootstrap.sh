#!/usr/bin/env bash
# =============================================================================
# NAIO OS — bootstrap.sh (Phase 7 signed update-channel installer)
# =============================================================================
# Remote-safe entrypoint. Downloads the release metadata and bundle files from
# nurse-ai-os.org into a temporary directory, verifies the signed manifest and
# artifact checksums, then runs install.sh with forwarded arguments.
#
# Example:
#   curl -fsSL https://nurse-ai-os.org/naio-os/bootstrap.sh | bash -s -- --self-test
#   curl -fsSL https://nurse-ai-os.org/naio-os/bootstrap.sh | bash -s -- \
#     --apply --soul ~/Downloads/naio-soul.json --projects ~/Downloads/naio-projects.json \
#     --target ./NAIO-Hermes-Profile
# =============================================================================
set -euo pipefail

BASE_URL="${NAIO_OS_BASE_URL:-https://nurse-ai-os.org/naio-os}"
WORKDIR="$(mktemp -d "${TMPDIR:-/tmp}/naio-os-bootstrap.XXXXXX")"
KEEP=0

cleanup() {
  if [[ "${KEEP}" != "1" ]]; then
    rm -rf "$WORKDIR"
  else
    echo "NAIO OS bootstrap directory kept: $WORKDIR"
  fi
}
trap cleanup EXIT

case " ${*:-} " in
  *" --keep-download "*) KEEP=1 ;;
esac

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "❌ Required command not found: $1" >&2
    exit 2
  fi
}

need python3

printf '\n%s\n' "=== NAIO OS bootstrap (Phase 7) ==="
echo "Source: $BASE_URL"
echo "Download directory: $WORKDIR"
echo "Doctrine: Agents propose. Humans judge. Nurses steward."
echo ""

python3 - "$BASE_URL" "$WORKDIR" <<'PY'
from pathlib import Path
import sys, urllib.request, yaml

base = sys.argv[1].rstrip('/')
root = Path(sys.argv[2])
root.mkdir(parents=True, exist_ok=True)

headers = {'User-Agent': 'naio-os-bootstrap/2.0.0-phase7', 'Cache-Control': 'no-cache'}

def fetch(rel: str) -> bytes:
    url = f"{base}/{rel}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=45) as r:
        if r.status != 200:
            raise SystemExit(f"download failed: {url} status={r.status}")
        return r.read()

for rel in ['release.json', 'release-history.json', 'manifest.sha256', 'manifest.sig']:
    (root / rel).write_bytes(fetch(rel))
    print(f"downloaded {rel}")

manifest_bytes = fetch('manifest.yaml')
(root / 'manifest.yaml').write_bytes(manifest_bytes)
manifest = yaml.safe_load(manifest_bytes.decode('utf-8'))
for item in manifest.get('contents', []):
    rel = item.get('path')
    if not rel or rel == 'manifest.yaml':
        continue
    dest = root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(fetch(rel))
    print(f"downloaded {rel}")
print(f"bundle_version={manifest.get('version')}")
PY

chmod +x "$WORKDIR/install.sh" "$WORKDIR/scripts/"*.sh "$WORKDIR/scripts/"*.py 2>/dev/null || true

echo ""
echo "▶ Bootstrap release verification"
python3 "$WORKDIR/scripts/verify-release.py"

echo ""
echo "▶ Bootstrap healthcheck"
python3 "$WORKDIR/scripts/healthcheck.py" --checksums-only

echo ""
echo "▶ Running NAIO OS installer with forwarded arguments"
cd "$WORKDIR"
exec bash ./install.sh "$@"
