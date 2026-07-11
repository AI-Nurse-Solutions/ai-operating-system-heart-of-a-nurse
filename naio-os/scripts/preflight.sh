#!/usr/bin/env bash
# =============================================================================
# NAIO OS — preflight.sh
# Detects OS, bash, python3, core deps, and optional Hermes presence.
# Exit 0 = ready; non-zero = blocked. Prints a human-readable report.
# Called by install.sh; safe to run standalone.
# =============================================================================
set -uo pipefail

PASS=0; WARN=0; FAIL=0
report() { printf "%-12s %s\n" "$1" "$2"; }
ok()   { report "✅ OK"     "$1"; PASS=$((PASS+1)); }
warn() { report "⚠️  WARN"   "$1"; WARN=$((WARN+1)); }
fail() { report "❌ FAIL"   "$1"; FAIL=$((FAIL+1)); }

printf "\n=== NAIO OS — preflight ===\n\n"

# --- Operating system ---
OS_KIND="unknown"
case "$(uname -s)" in
  Darwin*) OS_KIND="macOS $(sw_vers -productVersion 2>/dev/null || echo '?')"; ok "OS: $OS_KIND" ;;
  Linux*)  OS_KIND="Linux ($(uname -r 2>/dev/null))"; ok "OS: $OS_KIND" ;;
  MINGW*|MSYS*|CYGWIN*) OS_KIND="Windows (Git Bash/MSYS)"; warn "Windows via MSYS — Hermes Desktop support varies; proceed with caution" ;;
  *) fail "Unsupported OS: $(uname -s)" ;;
esac

# --- Architecture ---
ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|amd64) ok "Arch: $ARCH (x86_64)" ;;
  arm64|aarch64) ok "Arch: $ARCH (ARM)" ;;
  *) warn "Unrecognized arch: $ARCH" ;;
esac

# --- Shell ---
if [ -n "${BASH_VERSION:-}" ]; then
  ok "bash ${BASH_VERSION} at ${BASH}"
else
  warn "Not running under bash; scripts target bash 4+"
fi

# --- python3 ---
if command -v python3 >/dev/null 2>&1; then
  PYV="$(python3 -c 'import sys;print("%d.%d.%d"%sys.version_info[:3])' 2>/dev/null || echo '?')"
  PY_MAJOR_MINOR="$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null || echo 0)"
  PY_OK="$(python3 -c 'import sys;print(1 if sys.version_info>=(3,8) else 0)' 2>/dev/null || echo 0)"
  if [ "$PY_OK" = "1" ]; then ok "python3 $PYV"; else fail "python3 $PYV — need >= 3.8"; fi
else
  fail "python3 not found — required for validation + healthcheck"
fi

# --- Python deps (jsonschema, pyyaml) — optional but recommended ---
if [ "$PY_OK" = "1" ] 2>/dev/null; then
  if python3 -c 'import jsonschema' 2>/dev/null; then ok "python jsonschema"; else warn "python jsonschema missing — full schema validation will be skipped"; fi
  if python3 -c 'import yaml' 2>/dev/null;      then ok "python pyyaml";     else warn "python pyyaml missing — YAML parsing will be skipped"; fi
fi

# --- openssl (release signature verification) ---
# Content checksums are computed with python3's hashlib (required above);
# openssl is what verify-release.py needs to check manifest.sig.
if command -v openssl >/dev/null 2>&1; then
  ok "openssl (signature verification available)"
else
  fail "openssl not found — cannot verify the signed release (manifest.sig)"
fi

# --- curl (for one-line install) ---
if command -v curl >/dev/null 2>&1; then ok "curl"; else warn "curl missing — one-line install path unavailable"; fi

# --- Hermes Desktop (optional in Phase 2; required from Phase 3) ---
HERMES_FOUND="no"
if command -v hermes >/dev/null 2>&1; then
  HERMES_FOUND="yes"
  ok "hermes CLI on PATH"
elif [ -d "$HOME/.hermes" ]; then
  HERMES_FOUND="yes"
  ok "~/.hermes directory present"
else
  warn "Hermes Desktop not detected — Phase 2 runs in dry-run; Phase 3 requires Hermes"
fi

# --- Disk space sanity (>50 MB) ---
FREE_MB="$(df -m "${HOME:-/tmp}" 2>/dev/null | awk 'NR==2{print $4}')"
if [ -n "${FREE_MB:-}" ] && [ "$FREE_MB" -gt 50 ] 2>/dev/null; then
  ok "Free disk: ${FREE_MB} MB"
else
  warn "Could not confirm >50 MB free disk (got: ${FREE_MB:-unknown})"
fi

# --- Summary ---
printf "\n--- summary ---\n"
report "ok"   "$PASS"
report "warn" "$WARN"
report "fail" "$FAIL"
printf "\n"

if [ "$FAIL" -gt 0 ]; then
  echo "PREFLIGHT: BLOCKED — fix ❌ items above before installing."
  exit 2
fi
if [ "$WARN" -gt 0 ]; then
  echo "PREFLIGHT: PASS WITH WARNINGS — Phase 2 dry-run can continue; some checks skipped."
  exit 0
fi
echo "PREFLIGHT: PASS"
exit 0
