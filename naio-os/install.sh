#!/usr/bin/env bash
# =============================================================================
# NAIO OS — install.sh  (Phase 2: DRY-RUN distribution shell)
# =============================================================================
# Phase 2 scope: VALIDATE AND PLAN ONLY. No system mutation.
#   - preflight
#   - verify checksums against manifest
#   - validate naio-soul.json import (optional)
#   - validate naio-projects.json import (optional)
#   - show a plan of what WOULD be done
#   - run healthcheck
# =============================================================================

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
APPLY=0
SOUL=""
SOUL_PROVIDED=0
PROJECTS=""
PROJECTS_PROVIDED=0
WITH_CHECKSUMS=1

print_help() {
  cat <<'EOF'
NAIO OS installer (Phase 2 — dry-run)

Usage:
  ./install.sh [--dry-run] [--soul <path>] [--projects <path>] [--no-checksums] [--help]

Options:
  --dry-run          Validate and plan only; do not write anything. (DEFAULT)
  --apply            ⛔ Reserved for Phase 3. Refuses in Phase 2.
  --soul <path>      Path to naio-soul.json (from the SOUL Quiz).
  --projects <path>  Path to naio-projects.json (from the Life & Projects Quiz).
  --no-checksums     Skip sha256 verification against the manifest (not recommended).
  --help             Show this help.

Doctrine: Agents propose. Humans judge. Nurses steward.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) shift ;;
    --apply) APPLY=1; shift ;;
    --soul)
      if [[ $# -lt 2 ]]; then echo "--soul requires a path" >&2; exit 1; fi
      SOUL="$2"; SOUL_PROVIDED=1; shift 2 ;;
    --projects)
      if [[ $# -lt 2 ]]; then echo "--projects requires a path" >&2; exit 1; fi
      PROJECTS="$2"; PROJECTS_PROVIDED=1; shift 2 ;;
    --no-checksums) WITH_CHECKSUMS=0; shift ;;
    --help|-h) print_help; exit 0 ;;
    *) echo "Unknown option: $1" >&2; print_help; exit 1 ;;
  esac
done

cat <<'BANNER'

  ╔═══════════════════════════════════════════════════════════╗
  ║   NAIO OS — Nurse AI Operating System (Phase 2: dry-run)  ║
  ║   Governed AI for nurses, over Hermes Desktop             ║
  ╚═══════════════════════════════════════════════════════════╝

  Doctrine: Agents propose. Humans judge. Nurses steward.
  This phase VALIDATES AND PLANS ONLY. Nothing on your system will change.

BANNER

if [[ $APPLY -eq 1 ]]; then
  echo "❌ --apply is reserved for Phase 3 (live Hermes config + human gates)." >&2
  echo "   In Phase 2, the installer only validates and plans. Nothing is written." >&2
  exit 1
fi

echo "▶ STEP 1/6 — Preflight (environment check)"
if ! bash "$HERE/scripts/preflight.sh"; then
  echo "❌ Preflight blocked installation. Fix the issues above and re-run." >&2
  exit 2
fi

echo ""
echo "▶ STEP 2/6 — Verify checksums"
if [[ $WITH_CHECKSUMS -eq 1 ]]; then
  if python3 "$HERE/scripts/healthcheck.py" --checksums-only >/tmp/naio-hc-checksums.out 2>&1; then
    tail -n 5 /tmp/naio-hc-checksums.out
  else
    cat /tmp/naio-hc-checksums.out
    echo "❌ Checksum verification failed. Refusing to proceed." >&2
    exit 2
  fi
else
  echo "⚠️  Checksum verification SKIPPED by --no-checksums (not recommended)."
fi

echo ""
echo "▶ STEP 3/6 — Validate SOUL import (naio-soul.json)"
if [[ $SOUL_PROVIDED -eq 1 ]]; then
  if [[ ! -f "$SOUL" ]]; then
    echo "❌ naio-soul.json not found at: $SOUL" >&2
    exit 2
  fi
  if ! python3 "$HERE/scripts/import-soul.py" "$SOUL"; then
    echo "❌ SOUL import validation refused. See messages above." >&2
    exit 2
  fi
else
  echo "ℹ️  No --soul provided. Skipping SOUL import validation."
  echo "    (Provide one with: ./install.sh --soul path/to/naio-soul.json)"
fi

echo ""
echo "▶ STEP 4/6 — Validate Projects import (naio-projects.json)"
if [[ $PROJECTS_PROVIDED -eq 1 ]]; then
  if [[ ! -f "$PROJECTS" ]]; then
    echo "❌ naio-projects.json not found at: $PROJECTS" >&2
    exit 2
  fi
  if ! python3 "$HERE/scripts/import-projects.py" "$PROJECTS"; then
    echo "❌ Projects import validation refused. See messages above." >&2
    exit 2
  fi
else
  echo "ℹ️  No --projects provided. Skipping project import validation."
  echo "    (Provide one with: ./install.sh --projects path/to/naio-projects.json)"
fi

echo ""
echo "▶ STEP 5/6 — Plan (what Phase 3 WILL do with safe imports)"
cat <<'PLAN'
  In Phase 3 (live Hermes config), this installer would:
    1. Write your SOUL files (Core + per-sphere) into the Hermes config / vault.
    2. Write your project prompts (from naio-projects.json, if provided).
    3. Apply your EDENA tier ceilings per sphere to the Hermes control plane.
    4. Wire non-removable human gates (Green = every-output; Yellow = before-external-use).
    5. Enforce the no-PHI hard boundary at the harness layer.
    6. Seed stewardship cron rituals (weekly review, tier audit, wellbeing check).
    7. Run a final healthcheck and only then report success.

  In Phase 2 (now), NONE of the above runs. This was validation + planning only.
PLAN

echo ""
echo "▶ STEP 6/6 — Final healthcheck"
if python3 "$HERE/scripts/healthcheck.py" >/tmp/naio-hc-final.out 2>&1; then
  tail -n 4 /tmp/naio-hc-final.out
else
  cat /tmp/naio-hc-final.out
  echo "❌ Final healthcheck failed." >&2
  exit 1
fi

cat <<'DONE'

  ╔═══════════════════════════════════════════════════════════╗
  ║   ✅  NAIO OS Phase 2 dry-run complete.                   ║
  ║   The bundle and provided imports are safe.               ║
  ║   Nothing was written to your system.                     ║
  ╚═══════════════════════════════════════════════════════════╝

  Next steps:
    • Take the SOUL Quiz:   https://nurse-ai-os.org/soul-quiz.html
    • Map Life & Projects:  https://nurse-ai-os.org/life-quiz.html
    • Join the Lamp Huddle: https://nurse-ai-os.org/assets/lamp-huddle.md

  Phase 3 (live Hermes config) is in development.
  Doctrine: Agents propose. Humans judge. Nurses steward.
DONE

exit 0
