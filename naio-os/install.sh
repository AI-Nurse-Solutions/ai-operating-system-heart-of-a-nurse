#!/usr/bin/env bash
# =============================================================================
# NAIO OS — install.sh  (Phase 6: signed update channel + one-line UX)
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
SELF_TEST=0

print_help() {
  cat <<'EOF'
NAIO OS installer (Phase 6 — one-line UX + healthcheck/self-test harness)

Usage:
  ./install.sh [--dry-run] [--soul <path>] [--projects <path>] [--no-checksums]
  ./install.sh --apply --soul <path> [--projects <path>] --target <dir> [--force]
  ./install.sh --self-test

One-line remote self-test:
  curl -fsSL https://nurse-ai-os.org/naio-os/bootstrap.sh | bash -s -- --self-test

Options:
  --dry-run          Validate and plan only; do not write anything. (DEFAULT)
  --apply            Render a governed Hermes-ready profile bundle to --target.
  --target <dir>     Required with --apply. Explicit output directory; ~/.hermes is refused.
  --force            Replace existing --target directory. Refuses home and ~/.hermes.
  --soul <path>      Path to naio-soul.json (from the SOUL Quiz). Required for --apply.
  --projects <path>  Path to naio-projects.json (from the Life & Projects Quiz).
  --no-checksums     Skip sha256 verification against the manifest (not recommended).
  --self-test        Run the Phase 6 built-in smoke test and exit.
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
    --self-test) SELF_TEST=1; shift ;;
    --help|-h) print_help; exit 0 ;;
    *) echo "Unknown option: $1" >&2; print_help; exit 1 ;;
  esac
done

cat <<'BANNER'

  ╔═══════════════════════════════════════════════════════════╗
  ║   NAIO OS — Nurse AI Operating System (Phase 6)           ║
  ║   One-line installer + healthcheck/self-test harness       ║
  ╚═══════════════════════════════════════════════════════════╝

  Doctrine: Agents propose. Humans judge. Nurses steward.
  Default mode validates and plans. --apply renders only to an explicit target.

BANNER

if [[ $SELF_TEST -eq 1 ]]; then
  echo "▶ SELF-TEST — focused Phase 6 smoke test"
  exec python3 "$HERE/scripts/self-test.py"
fi

echo "▶ STEP 1/8 — Preflight (environment check)"
if ! bash "$HERE/scripts/preflight.sh"; then
  echo "❌ Preflight blocked installation. Fix the issues above and re-run." >&2
  exit 2
fi

echo ""
echo "▶ STEP 2/8 — Verify signed release metadata"
if python3 "$HERE/scripts/verify-release.py" >/tmp/naio-release-verify.out 2>&1; then
  tail -n 4 /tmp/naio-release-verify.out
else
  cat /tmp/naio-release-verify.out
  echo "❌ Release signature verification failed. Refusing to proceed." >&2
  exit 2
fi

echo ""
echo "▶ STEP 3/8 — Verify checksums"
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
echo "▶ STEP 4/8 — Validate SOUL import (naio-soul.json)"
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
echo "▶ STEP 5/8 — Validate Projects import (naio-projects.json)"
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
echo "▶ STEP 6/8 — Plan"
cat <<'PLAN'
  Phase 6 maps EDENA into a Hermes-ready profile bundle and execution plane, with a one-line installer and built-in self-test:
    1. Core SOUL.md and per-sphere SOUL files.
    2. EDENA runtime mapping: sphere ceilings → toolsets → human gates.
    3. Project system prompts from naio-projects.json, if provided.
    4. Tier-tagged starter skills with EDENA frontmatter.
    5. Cron ritual templates for Lamp Huddle, ledger review, tier audit, and knowledge digest.
    6. Suggested Hermes profile overlay, review-before-use.
    7. Signed release metadata and update-channel verification.
    8. Healthcheck + self-test harness before claims of success.

  Safety posture:
    • Writes only to --target when --apply is used.
    • Does NOT write to ~/.hermes directly.
    • Does NOT schedule cron jobs automatically.
    • Onboarding remains Green/Yellow only.
    • No PHI. No clinical decisions. Irreversible actions remain human-executed.
PLAN

if [[ $APPLY -eq 1 ]]; then
  echo ""
  echo "▶ STEP 7/8 — Apply (render governed profile bundle to target)"
  if [[ -z "$TARGET" ]]; then
    echo "❌ --apply requires --target <dir>" >&2
    exit 2
  fi
  RENDER_ARGS=("--soul" "$SOUL" "--target" "$TARGET")
  if [[ $PROJECTS_PROVIDED -eq 1 ]]; then RENDER_ARGS+=("--projects" "$PROJECTS"); fi
  if [[ $FORCE -eq 1 ]]; then RENDER_ARGS+=("--force"); fi
  if ! python3 "$HERE/scripts/render-profile.py" "${RENDER_ARGS[@]}"; then
    echo "❌ Phase 6 render failed." >&2
    exit 2
  fi
else
  echo ""
  echo "▶ STEP 7/8 — Apply skipped (dry-run default)"
  echo "  Nothing was written. To render a profile bundle, rerun with:"
  echo "  ./install.sh --apply --soul path/to/naio-soul.json --projects path/to/naio-projects.json --target ./NAIO-Hermes-Profile"
fi

echo ""
echo "▶ STEP 8/8 — Final healthcheck"
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
  ║   ✅  NAIO OS Phase 6 apply complete.                     ║
  ║   Governed profile + execution templates rendered.        ║
  ╚═══════════════════════════════════════════════════════════╝

  Target: $TARGET
  Review README-FIRST.md before copying anything into Hermes.
  Doctrine: Agents propose. Humans judge. Nurses steward.
DONE
else
  cat <<'DONE'

  ╔═══════════════════════════════════════════════════════════╗
  ║   ✅  NAIO OS Phase 6 dry-run complete.                   ║
  ║   Bundle and provided imports are safe. Nothing written.  ║
  ╚═══════════════════════════════════════════════════════════╝

  Doctrine: Agents propose. Humans judge. Nurses steward.
DONE
fi

exit 0
