#!/usr/bin/env bash
# =============================================================================
# NAIO OS — bootstrap.sh (Phase 23 signed commercial activation installer)
# =============================================================================
# Remote-safe entrypoint. Downloads the release metadata and bundle files from
# nurse-ai-os.org into a temporary directory, verifies the release public key
# against the fingerprint PINNED IN THIS FILE, verifies the signed manifest
# and every artifact checksum, and only then executes the downloaded installer.
#
# Trust model:
#   • NAIO_OS_PUBKEY_SHA256 below pins the SHA-256 of
#     config/naio-os-release-public.pem, so a compromised or spoofed server
#     cannot substitute its own key + signature: nothing downloaded is
#     executed until the key matches this pin and the manifest signature
#     verifies against it.
#   • Prefer download-then-inspect over piping straight to bash, and compare
#     this file against the copy in the source repository
#     (github.com/AI-Nurse-Solutions/ai-operating-system-heart-of-a-nurse)
#     for an out-of-band check of the pin itself.
#   • On key rotation: ship the new key, update NAIO_OS_PUBKEY_SHA256 here in
#     the same release, and record the rotation in release-history.json.
#
# Example:
#   curl -fsSLO https://nurse-ai-os.org/naio-os/bootstrap.sh   # inspect first
#   bash bootstrap.sh --self-test
#   bash bootstrap.sh \
#     --apply --soul ~/Downloads/naio-soul.json --projects ~/Downloads/naio-projects.json \
#     --target ./NAIO-Hermes-Profile
# =============================================================================
set -euo pipefail

BASE_URL="${NAIO_OS_BASE_URL:-https://nurse-ai-os.org/naio-os}"
# SHA-256 of config/naio-os-release-public.pem — the root of trust for this
# bootstrap. Update ONLY on a deliberate, documented key rotation.
NAIO_OS_PUBKEY_SHA256="9c1eae2f1cf585734ab913aae1101abed1ac83676e972f20482520df6436861f"
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
need openssl

printf '\n%s\n' "=== NAIO OS bootstrap (Phase 23) ==="
echo "Source: $BASE_URL"
echo "Download directory: $WORKDIR"
echo "Doctrine: Agents propose. Humans judge. Nurses steward."
echo ""

python3 - "$BASE_URL" "$WORKDIR" <<'PY'
from pathlib import Path
import hashlib, sys, urllib.request, yaml

base = sys.argv[1].rstrip('/')
root = Path(sys.argv[2])
root.mkdir(parents=True, exist_ok=True)

headers = {'User-Agent': 'naio-os-bootstrap/2.0.0-phase23', 'Cache-Control': 'no-cache'}

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

# Verify each artifact against the checksum the manifest declares for it.
# This proves internal consistency at download time; authenticity of the
# manifest itself is proven right after by the pinned-key signature check.
for item in manifest.get('contents', []):
    rel = item.get('path')
    if not rel or rel == 'manifest.yaml':
        continue
    data = fetch(rel)
    want = item.get('sha256')
    if want:
        got = hashlib.sha256(data).hexdigest()
        if got != want:
            raise SystemExit(f"❌ checksum mismatch for {rel}: manifest={want} downloaded={got}")
    dest = root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    print(f"downloaded {rel} (checksum ok)" if want else f"downloaded {rel}")
print(f"bundle_version={manifest.get('version')}")
PY

echo ""
echo "▶ Bootstrap trust anchor — pinned public key fingerprint"
PUBKEY_FILE="$WORKDIR/config/naio-os-release-public.pem"
if [[ ! -f "$PUBKEY_FILE" ]]; then
  echo "❌ Release public key missing from download: config/naio-os-release-public.pem" >&2
  exit 2
fi
# hashlib rather than `openssl dgst -r`: the -r flag is missing from some
# LibreSSL builds (macOS's default openssl), and python3 is already required.
ACTUAL_PUBKEY_SHA256="$(python3 -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" "$PUBKEY_FILE")"
if [[ "$ACTUAL_PUBKEY_SHA256" != "$NAIO_OS_PUBKEY_SHA256" ]]; then
  echo "❌ RELEASE KEY MISMATCH — refusing to run anything downloaded." >&2
  echo "   pinned:     $NAIO_OS_PUBKEY_SHA256" >&2
  echo "   downloaded: $ACTUAL_PUBKEY_SHA256" >&2
  echo "   The server's release key does not match the fingerprint pinned in bootstrap.sh." >&2
  echo "   Unless a key rotation was announced, treat this as a compromised source." >&2
  exit 2
fi
echo "✅ Public key matches pinned fingerprint."

echo ""
echo "▶ Bootstrap signature check — manifest.yaml against the pinned key"
if ! openssl dgst -sha256 -verify "$PUBKEY_FILE" -signature "$WORKDIR/manifest.sig" "$WORKDIR/manifest.yaml" >/dev/null 2>&1; then
  echo "❌ manifest.sig does not verify against the pinned release key. Refusing to proceed." >&2
  exit 2
fi
echo "✅ Manifest signature verified with pinned key."

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
