#!/usr/bin/env bash
# =============================================================================
# NAIO OS — install.sh  (Phase 20: Partner / Sponsor Briefing Pack)
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
CHECK_UPDATE=0
RECOVERY_DRILL=0
ACTIVATION_CHECK=0
LAUNCH_CHECK=0
COHORT_CHECK=0
EVIDENCE_CHECK=0
CONTRIBUTION_CHECK=0
PILOT_CHECK=0
READINESS_CHECK=0
REGISTRY_CHECK=0
ORCHESTRATION_CHECK=0
GOVERNANCE_CHECK=0
PARTNER_CHECK=0
STEWARDSHIP_CHECK=0

print_help() {
  cat <<'EOF'
NAIO OS installer (Phase 20 — Partner / Sponsor Briefing Pack + healthcheck/self-test harness)

Usage:
  ./install.sh [--dry-run] [--soul <path>] [--projects <path>] [--no-checksums]
  ./install.sh --apply --soul <path> [--projects <path>] --target <dir> [--force]
  ./install.sh --self-test
  ./install.sh --check-update
  ./install.sh --recovery-drill --target <rendered-profile-dir>
  ./install.sh --activation-check --target <rendered-profile-dir>
  ./install.sh --launch-check --target <rendered-profile-dir>
  ./install.sh --cohort-check --target <rendered-profile-dir>
  ./install.sh --evidence-check --target <rendered-profile-dir>
  ./install.sh --contribution-check --target <rendered-profile-dir>
  ./install.sh --pilot-check --target <rendered-profile-dir>
  ./install.sh --readiness-check --target <rendered-profile-dir>
  ./install.sh --registry-check --target <rendered-profile-dir>
  ./install.sh --orchestration-check --target <rendered-profile-dir>
  ./install.sh --governance-check --target <rendered-profile-dir>
  ./install.sh --partner-check --target <rendered-profile-dir>
  ./install.sh --stewardship-check --target <rendered-profile-dir>

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
  --self-test        Run the Phase 20 built-in smoke test and exit.
  --check-update     Verify release history and compare the advisory update channel; no install/mutation.
  --recovery-drill   Run a local-only recovery snapshot/verify/extract/plan drill for --target.
  --activation-check  Verify first-run START-HERE and 7-day activation readiness for --target.
  --launch-check     Verify no-PHI public launch pack readiness for --target.
  --cohort-check      Verify no-PHI cohort/instructor readiness for --target.
  --evidence-check    Verify no-PHI EDENA evidence trail readiness for --target.
  --contribution-check Verify no-PHI NIN contribution flow readiness for --target.
  --pilot-check        Verify non-clinical institutional pilot readiness for --target.
  --readiness-check    Verify EDENA readiness review posture for --target.
  --registry-check     Verify NAIO Agent Registry listing posture for --target.
  --orchestration-check Verify Florence-X orchestration preview posture for --target.
  --governance-check    Verify Governance Board / Steward Council advisory posture for --target.
  --partner-check       Verify Partner / Sponsor Briefing informational posture for --target.
  --stewardship-check   Verify Institutional Stewardship Operating Model advisory posture for --target.
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
    --check-update) CHECK_UPDATE=1; shift ;;
    --recovery-drill) RECOVERY_DRILL=1; shift ;;
    --activation-check) ACTIVATION_CHECK=1; shift ;;
    --launch-check) LAUNCH_CHECK=1; shift ;;
    --cohort-check) COHORT_CHECK=1; shift ;;
    --evidence-check) EVIDENCE_CHECK=1; shift ;;
    --contribution-check) CONTRIBUTION_CHECK=1; shift ;;
    --pilot-check) PILOT_CHECK=1; shift ;;
    --readiness-check) READINESS_CHECK=1; shift ;;
    --registry-check) REGISTRY_CHECK=1; shift ;;
    --orchestration-check) ORCHESTRATION_CHECK=1; shift ;;
    --governance-check) GOVERNANCE_CHECK=1; shift ;;
    --partner-check) PARTNER_CHECK=1; shift ;;
    --stewardship-check) STEWARDSHIP_CHECK=1; shift ;;
    --help|-h) print_help; exit 0 ;;
    *) echo "Unknown option: $1" >&2; print_help; exit 1 ;;
  esac
done

cat <<'BANNER'

  ╔═══════════════════════════════════════════════════════════╗
  ║   NAIO OS — Nurse AI Operating System (Phase 20)           ║
  ║   One-line installer + healthcheck/self-test harness       ║
  ╚═══════════════════════════════════════════════════════════╝

  Doctrine: Agents propose. Humans judge. Nurses steward.
  Default mode validates and plans. --apply renders only to an explicit target.

BANNER

if [[ $SELF_TEST -eq 1 ]]; then
  echo "▶ SELF-TEST — focused Phase 20 smoke test"
  exec python3 "$HERE/scripts/self-test.py"
fi

if [[ $CHECK_UPDATE -eq 1 ]]; then
  echo "▶ CHECK UPDATE — Phase 20 advisory, no mutation"
  exec python3 "$HERE/scripts/check-update.py"
fi

if [[ $RECOVERY_DRILL -eq 1 ]]; then
  echo "▶ RECOVERY DRILL — Phase 20 local-only snapshot/verify/extract/plan"
  if [[ -z "$TARGET" ]]; then
    echo "❌ --recovery-drill requires --target <rendered-profile-dir>" >&2
    exit 2
  fi
  exec python3 "$HERE/scripts/recovery.py" --drill --profile "$TARGET"
fi

if [[ $ACTIVATION_CHECK -eq 1 ]]; then
  echo "▶ ACTIVATION CHECK — Phase 20 first-run readiness, no mutation"
  if [[ -z "$TARGET" ]]; then
    echo "❌ --activation-check requires --target <rendered-profile-dir>" >&2
    exit 2
  fi
  exec python3 "$HERE/scripts/activation.py" --profile "$TARGET"
fi

if [[ $LAUNCH_CHECK -eq 1 ]]; then
  echo "▶ LAUNCH CHECK — Phase 20 public launch readiness, no mutation"
  if [[ -z "$TARGET" ]]; then
    echo "❌ --launch-check requires --target <rendered-profile-dir>" >&2
    exit 2
  fi
  exec python3 "$HERE/scripts/launch.py" --profile "$TARGET"
fi

if [[ $COHORT_CHECK -eq 1 ]]; then
  echo "▶ COHORT CHECK — Phase 20 instructor/cohort readiness, no mutation"
  if [[ -z "$TARGET" ]]; then
    echo "❌ --cohort-check requires --target <rendered-profile-dir>" >&2
    exit 2
  fi
  exec python3 "$HERE/scripts/cohort.py" --profile "$TARGET"
fi

if [[ $EVIDENCE_CHECK -eq 1 ]]; then
  echo "▶ EVIDENCE CHECK — Phase 20 EDENA evidence trail readiness, no mutation"
  if [[ -z "$TARGET" ]]; then
    echo "❌ --evidence-check requires --target <rendered-profile-dir>" >&2
    exit 2
  fi
  exec python3 "$HERE/scripts/evidence.py" --profile "$TARGET"
fi

if [[ $CONTRIBUTION_CHECK -eq 1 ]]; then
  echo "▶ CONTRIBUTION CHECK — Phase 20 NIN community contribution readiness, no mutation"
  if [[ -z "$TARGET" ]]; then
    echo "❌ --contribution-check requires --target <rendered-profile-dir>" >&2
    exit 2
  fi
  exec python3 "$HERE/scripts/contribute.py" --profile "$TARGET"
fi

if [[ $PILOT_CHECK -eq 1 ]]; then
  echo "▶ PILOT CHECK — Phase 20 institutional pilot readiness, no mutation"
  if [[ -z "$TARGET" ]]; then
    echo "❌ --pilot-check requires --target <rendered-profile-dir>" >&2
    exit 2
  fi
  exec python3 "$HERE/scripts/pilot.py" --profile "$TARGET"
fi

if [[ $READINESS_CHECK -eq 1 ]]; then
  echo "▶ READINESS CHECK — Phase 20 EDENA readiness review, no mutation"
  if [[ -z "$TARGET" ]]; then
    echo "❌ --readiness-check requires --target <rendered-profile-dir>" >&2
    exit 2
  fi
  exec python3 "$HERE/scripts/readiness.py" --profile "$TARGET"
fi

if [[ $REGISTRY_CHECK -eq 1 ]]; then
  echo "▶ REGISTRY CHECK — Phase 20 NAIO Agent Registry listing posture, no mutation"
  if [[ -z "$TARGET" ]]; then
    echo "❌ --registry-check requires --target <rendered-profile-dir>" >&2
    exit 2
  fi
  exec python3 "$HERE/scripts/registry.py" --profile "$TARGET"
fi

if [[ $ORCHESTRATION_CHECK -eq 1 ]]; then
  echo "▶ ORCHESTRATION CHECK — Phase 20 Florence-X dry-run preview, no mutation"
  if [[ -z "$TARGET" ]]; then
    echo "❌ --orchestration-check requires --target <rendered-profile-dir>" >&2
    exit 2
  fi
  exec python3 "$HERE/scripts/orchestration.py" --profile "$TARGET"
fi

if [[ $GOVERNANCE_CHECK -eq 1 ]]; then
  echo "▶ GOVERNANCE CHECK — Phase 20 advisory Steward Council posture, no mutation"
  if [[ -z "$TARGET" ]]; then
    echo "❌ --governance-check requires --target <rendered-profile-dir>" >&2
    exit 2
  fi
  exec python3 "$HERE/scripts/governance.py" --profile "$TARGET"
fi

if [[ $PARTNER_CHECK -eq 1 ]]; then
  echo "▶ PARTNER CHECK — Phase 20 informational partner/sponsor briefing posture, no mutation"
  if [[ -z "$TARGET" ]]; then
    echo "❌ --partner-check requires --target <rendered-profile-dir>" >&2
    exit 2
  fi
  exec python3 "$HERE/scripts/partner.py" --profile "$TARGET"
fi

if [[ $STEWARDSHIP_CHECK -eq 1 ]]; then
  echo "▶ STEWARDSHIP CHECK — Phase 20 advisory institutional operating model posture, no mutation"
  if [[ -z "$TARGET" ]]; then
    echo "❌ --stewardship-check requires --target <rendered-profile-dir>" >&2
    exit 2
  fi
  exec python3 "$HERE/scripts/stewardship.py" --profile "$TARGET"
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
  Phase 20 maps EDENA into a Hermes-ready profile bundle and execution plane, with a one-line installer and built-in self-test:
    1. Core SOUL.md and per-sphere SOUL files.
    2. EDENA runtime mapping: sphere ceilings → toolsets → human gates.
    3. Project system prompts from naio-projects.json, if provided.
    4. Tier-tagged starter skills with EDENA frontmatter.
    5. Cron ritual templates for Lamp Huddle, ledger review, tier audit, and knowledge digest.
    6. Suggested Hermes profile overlay, review-before-use.
    7. Signed release metadata, rollback protection, and update-channel verification.
    8. Healthcheck + self-test harness before claims of success.
    9. Public launch pack for no-PHI, no-overclaim sharing.
    10. Cohort/Instructor Mode for no-PHI, non-certifying facilitation.
    11. EDENA Evidence Trail for no-PHI evidence of learning, not certification.
    12. NIN Community Contribution Flow for sanitized, human-reviewed community submissions.
    13. Institutional Pilot Pack for non-clinical small-group adoption without deployment or endorsement claims.
    14. EDENA Micro-Credential Readiness Pack for formative human review without certification, badges, or clinical-readiness claims.
    15. NAIO Agent Registry Pack for human-reviewed learning listings without endorsement, procurement, deployment, or clinical-readiness claims.
    16. Florence-X Orchestration Preview Pack for dry-run multi-agent coordination without shared memory runtime or autonomous handoffs.
    17. Governance Board / Steward Council Pack for advisory human governance without institutional authority or automatic approvals.
    18. Partner / Sponsor Briefing Pack for informational collaboration conversations without solicitation, approval, funding, procurement, clinical deployment, or automatic outreach.
    19. Institutional Stewardship Operating Model Pack for advisory cadence without legal, compliance, procurement, staffing, clinical deployment, or automatic implementation authority.

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
    echo "❌ Phase 20 render failed." >&2
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
  ║   ✅  NAIO OS Phase 20 apply complete.                     ║
  ║   Governed profile + execution templates rendered.        ║
  ╚═══════════════════════════════════════════════════════════╝

  Target: $TARGET
  Review README-FIRST.md, 10-Public-Launch/, 11-Cohort-Mode/, 12-Evidence-Trail/, and 13-Contribution-Flow/, and 14-Institutional-Pilot/, and 15-EDENA-Readiness/, and 16-Agent-Registry/, and 17-Florence-X-Orchestration/, and 18-Governance-Board/, and 19-Partner-Briefing/, and 20-Stewardship-Operating-Model/ before copying, sharing, facilitating, documenting, contributing, piloting, requesting readiness review, drafting registry listings, rehearsing orchestration, convening governance review, briefing partners/sponsors, or coordinating institutional stewardship.
  Doctrine: Agents propose. Humans judge. Nurses steward.
DONE
else
  cat <<'DONE'

  ╔═══════════════════════════════════════════════════════════╗
  ║   ✅  NAIO OS Phase 20 dry-run complete.                   ║
  ║   Bundle and provided imports are safe. Nothing written.  ║
  ╚═══════════════════════════════════════════════════════════╝

  Doctrine: Agents propose. Humans judge. Nurses steward.
DONE
fi

exit 0
