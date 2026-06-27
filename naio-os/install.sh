#!/usr/bin/env bash
# =============================================================================
# NAIO OS — install.sh  (Phase 3: governed profile renderer)
# =============================================================================
# Default: dry-run validate + plan. Apply mode is real but safe:
#   ./install.sh --apply --soul naio-soul.json --projects naio-projects.json --target ./NAIO-Hermes-Profile
# It writes ONLY to the explicit target directory; never directly to ~/.hermes.
# =============================================================================
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
APPLY=0
FORCE=0
SOUL=""
SOUL_PROVIDED=0
PROJECTS=""
PROJECTS_PROVIDED=0
TARGET=""
WITH_CHECKSUMS=1

print_help() {
  cat <<'EOF'
NAIO OS installer (Phase 3 — governed profile renderer)

Usage:
  ./install.sh [--dry-run] [--soul <path>] [--projects <path>] [--no-checksums]
  ./install.sh --apply --soul <path> [--projects <path>] --target <dir> [--force]

Options:
  --dry-run          Validate and plan only; do not write anything. (DEFAULT)
  --apply            Render a governed Hermes-ready profile bundle to --target.
  --target <dir>     Required with --apply. Explicit output directory; ~/.hermes is refused.
  --force            Replace existing --target directory. Refuses home and ~/.hermes.
  --soul <path>      Path to naio-soul.json (from the SOUL Quiz). Required for --apply.
  --projects <path>  Path to naio-projects.json (from the Life & Projects Quiz).
  --no-checksums     Skip sha256 verification against the manifest (not recommended).
  --help             Show this help.

Doctrine: Agents propose. Humans judge. Nurses steward.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) APPLY=0; shift ;;
    --apply) APPLY=1; shift ;;
    --force) FORCE=1; shift ;;
    --target)
      if [[ $# -lt 2 ]]; then echo "--target requires a directory" >&2; exit 1; fi
      TARGET="$2"; shift 2 ;;
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
  ║   NAIO OS — Nurse AI Operating System (Phase 3)           ║
  ║   EDENA → Hermes profile mapping with human gates         ║
  ╚═══════════════════════════════════════════════════════════╝

  Doctrine: Agents propose. Humans judge. Nurses steward.
  Default mode validates and plans. --apply renders only to an explicit target.

BANNER

echo "▶ STEP 1/7 — Preflight (environment check)"
if ! bash "$HERE/scripts/preflight.sh"; then
  echo "❌ Preflight blocked installation. Fix the issues above and re-run." >&2
  exit 2
fi

echo ""
echo "▶ STEP 2/7 — Verify checksums"
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
echo "▶ STEP 3/7 — Validate SOUL import (naio-soul.json)"
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
  if [[ $APPLY -eq 1 ]]; then
    echo "❌ --apply requires --soul path/to/naio-soul.json" >&2
    exit 2
  fi
  echo "ℹ️  No --soul provided. Skipping SOUL import validation."
fi

echo ""
echo "▶ STEP 4/7 — Validate Projects import (naio-projects.json)"
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
  echo "ℹ️  No --projects provided. Project prompt rendering will be skipped."
fi

echo ""
echo "▶ STEP 5/7 — Plan"
cat <<'PLAN'
  Phase 3 maps EDENA into a Hermes-ready profile bundle:
    1. Core SOUL.md and per-sphere SOUL files.
    2. EDENA runtime mapping: sphere ceilings → toolsets → human gates.
    3. Project system prompts from naio-projects.json, if provided.
    4. Human-gates config: Green every-output, Yellow before-external-use.
    5. Suggested Hermes profile overlay, review-before-use.

  Safety posture:
    • Writes only to --target when --apply is used.
    • Does NOT write to ~/.hermes directly.
    • Onboarding remains Green/Yellow only.
    • No PHI. No clinical decisions. Irreversible actions remain human-executed.
PLAN

if [[ $APPLY -eq 1 ]]; then
  echo ""
  echo "▶ STEP 6/7 — Apply (render governed profile bundle to target)"
  if [[ -z "$TARGET" ]]; then
    echo "❌ --apply requires --target <dir>" >&2
    exit 2
  fi
  RENDER_ARGS=("--soul" "$SOUL" "--target" "$TARGET")
  if [[ $PROJECTS_PROVIDED -eq 1 ]]; then RENDER_ARGS+=("--projects" "$PROJECTS"); fi
  if [[ $FORCE -eq 1 ]]; then RENDER_ARGS+=("--force"); fi
  if ! python3 "$HERE/scripts/render-profile.py" "${RENDER_ARGS[@]}"; then
    echo "❌ Phase 3 render failed." >&2
    exit 2
  fi
else
  echo ""
  echo "▶ STEP 6/7 — Apply skipped (dry-run default)"
  echo "  Nothing was written. To render a profile bundle, rerun with:"
  echo "  ./install.sh --apply --soul path/to/naio-soul.json --projects path/to/naio-projects.json --target ./NAIO-Hermes-Profile"
fi

echo ""
echo "▶ STEP 7/7 — Final healthcheck"
if python3 "$HERE/scripts/healthcheck.py" >/tmp/naio-hc-final.out 2>&1; then
  tail -n 4 /tmp/naio-hc-final.out
else
  cat /tmp/naio-hc-final.out
  echo "❌ Final healthcheck failed." >&2
  exit 1
fi

if [[ $APPLY -eq 1 ]]; then
  cat <<DONE

  ╔═══════════════════════════════════════════════════════════╗
  ║   ✅  NAIO OS Phase 3 apply complete.                     ║
  ║   Governed profile bundle rendered to target only.        ║
  ╚═══════════════════════════════════════════════════════════╝

  Target: $TARGET
  Review README-FIRST.md before copying anything into Hermes.
  Doctrine: Agents propose. Humans judge. Nurses steward.
DONE
else
  cat <<'DONE'

  ╔═══════════════════════════════════════════════════════════╗
  ║   ✅  NAIO OS Phase 3 dry-run complete.                   ║
  ║   Bundle and provided imports are safe. Nothing written.  ║
  ╚═══════════════════════════════════════════════════════════╝

  Doctrine: Agents propose. Humans judge. Nurses steward.
DONE
fi

exit 0
