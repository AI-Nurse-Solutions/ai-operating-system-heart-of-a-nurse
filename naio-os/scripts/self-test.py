#!/usr/bin/env python3
"""
NAIO OS — self-test.py (Phase 23)

Focused verification harness for the downloadable Nurse AI OS bundle. This is
not a substitute for a repository test suite; it is a user-facing smoke test
that proves the installer can validate imports, render a target-only profile
bundle, and refuse unsafe paths/tiers.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - healthcheck catches this in normal use
    yaml = None

ROOT = Path(__file__).resolve().parent.parent
PASS = 0
FAIL = 0


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)


def ok(msg: str) -> None:
    global PASS
    PASS += 1
    print(f"  ✅ {msg}")


def fail(msg: str) -> None:
    global FAIL
    FAIL += 1
    print(f"  ❌ {msg}")


def check(msg: str, condition: bool, detail: str = "") -> None:
    if condition:
        ok(msg if not detail else f"{msg} ({detail})")
    else:
        fail(msg if not detail else f"{msg} ({detail})")


def sample_soul() -> dict:
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-06-27T00:00:00Z",
        "generator": "soul-quiz",
        "identity": {
            "name": "Maria",
            "role": "staff",
            "role_label": "Staff Nurse",
            "one_liner": "ICU nurse building safe AI routines",
            "always_remember": "No PHI. No clinical decisions.",
        },
        "voice": {
            "length": "Conversational",
            "formality": "Professional",
            "pushback": "Direct but kind",
            "avoid": "Hype",
        },
        "values": ["dignity", "safety", "learning"],
        "spheres": ["personal", "professional", "community"],
        "interests": [],
        "tier_ceilings": {
            "personal": "green",
            "professional": "yellow",
            "community": "yellow",
        },
        "boundaries": {
            "no_phi_confirmed": True,
            "no_clinical_decisions_confirmed": True,
            "confidential_list": [],
            "wellbeing_rule": "Pause when overwhelmed.",
            "decisions_always_mine": ["clinical decisions", "sending external messages"],
            "drafts_without_asking": ["notes", "outlines"],
        },
        "doctrine": {
            "edena": "edena-policy@2.0.0",
            "florence_x": "florence-x@2.0.0",
            "core_line": "Agents propose. Humans judge. Nurses steward.",
        },
    }


def sample_projects() -> dict:
    return {
        "schema_version": "1.0.0",
        "generated_at": "2026-06-27T00:00:00Z",
        "generator": "life-quiz",
        "identity": {"name": "Maria"},
        "spheres_active": ["personal", "professional"],
        "project_count": 2,
        "projects": [
            {
                "name": "Health and wellbeing",
                "suggested_prompt_name": "Weekly Energy Review",
                "sphere": "personal",
                "sphere_label": "Personal / Family",
                "edena_tier": "green",
                "slug": "health-wellbeing",
                "help": "sleep planning",
                "goal_90_days": "consistent rest",
                "human_gate": "every-output",
                "reversibility": "reversible",
                "file_path": "04-Projects/health-wellbeing.md",
            },
            {
                "name": "Meeting prep",
                "suggested_prompt_name": "Meeting Prep Brief",
                "sphere": "professional",
                "sphere_label": "Professional",
                "edena_tier": "yellow",
                "slug": "meeting-prep",
                "help": "agenda prep",
                "goal_90_days": "meetings are calmer",
                "human_gate": "before-external-use",
                "reversibility": "reversible",
                "file_path": "04-Projects/meeting-prep.md",
            },
        ],
    }


def verify_target(target: Path) -> None:
    expected = [
        "START-HERE.md",
        "README-FIRST.md",
        "SOUL.md",
        ".hermes.md",
        "spheres/personal.SOUL.md",
        "spheres/professional.SOUL.md",
        "spheres/community.SOUL.md",
        "projects/health-wellbeing.SYSTEM.md",
        "projects/meeting-prep.SYSTEM.md",
        "skills/lamp-huddle-steward/SKILL.md",
        "skills/weekly-ledger-review/SKILL.md",
        "skills/project-next-action-brief/SKILL.md",
        "skills/knowledge-inbox-digest/SKILL.md",
        "skills/edena-tier-audit/SKILL.md",
        "cron/rituals.yaml",
        "cron/README.md",
        "cron/prompts/weekly-lamp-huddle-review.md",
        "cron/prompts/monday-project-next-actions.md",
        "cron/prompts/monthly-edena-tier-audit.md",
        "cron/prompts/knowledge-inbox-digest.md",
        "config/edena-runtime.yaml",
        "config/human-gates.yaml",
        "config/hermes-profile.patch.yaml",
        "logs/render-report.json",
        "07-First-Week/Day-1-Setup.md",
        "07-First-Week/Day-2-SOUL-Review.md",
        "07-First-Week/Day-3-Project-Triage.md",
        "07-First-Week/Day-4-Lamp-Huddle.md",
        "07-First-Week/Day-5-Knowledge-Inbox.md",
        "07-First-Week/Day-6-Boundary-Review.md",
        "07-First-Week/Day-7-Weekly-Ledger.md",
        "10-Public-Launch/README.md",
        "10-Public-Launch/Launch-Checklist.md",
        "10-Public-Launch/Safety-Boundaries.md",
        "10-Public-Launch/FAQ.md",
        "10-Public-Launch/Founder-Note.md",
        "10-Public-Launch/Demo-Script.md",
        "10-Public-Launch/Social-Post-LinkedIn.md",
        "10-Public-Launch/Social-Post-Instagram-Facebook.md",
        "10-Public-Launch/Email-Invite.md",
        "11-Cohort-Mode/README.md",
        "11-Cohort-Mode/Instructor-Guide.md",
        "11-Cohort-Mode/Cohort-Launch-Checklist.md",
        "11-Cohort-Mode/Week-1-Facilitation-Plan.md",
        "11-Cohort-Mode/Week-2-Facilitation-Plan.md",
        "11-Cohort-Mode/Week-3-Facilitation-Plan.md",
        "11-Cohort-Mode/Week-4-Facilitation-Plan.md",
        "11-Cohort-Mode/Participant-Readiness-Rubric.md",
        "11-Cohort-Mode/Office-Hours-Question-Triage.md",
        "11-Cohort-Mode/Completion-Reflection.md",
        "12-Evidence-Trail/README.md",
        "12-Evidence-Trail/Evidence-Capture-Guide.md",
        "12-Evidence-Trail/EDENA-Lens-Reflection.md",
        "12-Evidence-Trail/Artifact-Log.md",
        "12-Evidence-Trail/Human-Gate-Ledger.md",
        "12-Evidence-Trail/Boundary-Incident-Template.md",
        "12-Evidence-Trail/Portfolio-Index.md",
        "12-Evidence-Trail/Facilitator-Review-Notes.md",
        "12-Evidence-Trail/Evidence-Export-Checklist.md",
        "12-Evidence-Trail/Not-Certification-Statement.md",
        "13-Contribution-Flow/README.md",
        "13-Contribution-Flow/Contribution-Intake-Guide.md",
        "13-Contribution-Flow/Sanitization-Checklist.md",
        "13-Contribution-Flow/Contribution-Template.md",
        "13-Contribution-Flow/EDENA-Review-Rubric.md",
        "13-Contribution-Flow/Attribution-and-Consent.md",
        "13-Contribution-Flow/Community-Use-License.md",
        "13-Contribution-Flow/Reviewer-Triage-Queue.md",
        "13-Contribution-Flow/Not-Endorsement-Statement.md",
        "13-Contribution-Flow/Contributor-Thank-You.md",
        "14-Institutional-Pilot/README.md",
        "14-Institutional-Pilot/Pilot-Charter.md",
        "14-Institutional-Pilot/Stakeholder-Brief.md",
        "14-Institutional-Pilot/Risk-Register.md",
        "14-Institutional-Pilot/No-PHI-Pilot-Boundary.md",
        "14-Institutional-Pilot/Participant-Onboarding-Checklist.md",
        "14-Institutional-Pilot/Weekly-Pilot-Ledger.md",
        "14-Institutional-Pilot/Pilot-Outcome-Reflection.md",
        "14-Institutional-Pilot/Governance-Escalation-Path.md",
        "14-Institutional-Pilot/Not-Clinical-Deployment-Statement.md",
        "14-Institutional-Pilot/Pilot-Closeout-Brief.md",
        "15-EDENA-Readiness/README.md",
        "15-EDENA-Readiness/Readiness-Overview.md",
        "15-EDENA-Readiness/Eligibility-Self-Check.md",
        "15-EDENA-Readiness/Evidence-Map.md",
        "15-EDENA-Readiness/Stewardship-Reflection.md",
        "15-EDENA-Readiness/Boundary-Competence-Ledger.md",
        "15-EDENA-Readiness/Reviewer-Guide.md",
        "15-EDENA-Readiness/Readiness-Rubric.md",
        "15-EDENA-Readiness/Remediation-Plan.md",
        "15-EDENA-Readiness/Non-Certification-Statement.md",
        "15-EDENA-Readiness/Readiness-Review-Cover-Sheet.md",
        "15-EDENA-Readiness/Badge-Deferral-Notice.md",
        "16-Agent-Registry/README.md",
        "16-Agent-Registry/Registry-Overview.md",
        "16-Agent-Registry/Agent-Intake-Card.md",
        "16-Agent-Registry/Source-Verification-Checklist.md",
        "16-Agent-Registry/EDENA-Agent-Evaluation.md",
        "16-Agent-Registry/Risk-and-Boundary-Review.md",
        "16-Agent-Registry/Nurse-Use-Case-Fit.md",
        "16-Agent-Registry/Registry-Listing-Template.md",
        "16-Agent-Registry/Not-Endorsement-Statement.md",
        "16-Agent-Registry/Human-Review-Queue.md",
        "16-Agent-Registry/Registry-Change-Log.md",
        "16-Agent-Registry/Retirement-and-Recheck-Plan.md",
        "17-Florence-X-Orchestration/README.md",
        "17-Florence-X-Orchestration/Orchestration-Overview.md",
        "17-Florence-X-Orchestration/Shared-Intent-Card.md",
        "17-Florence-X-Orchestration/Shared-Context-Card.md",
        "17-Florence-X-Orchestration/Semantic-State-Card.md",
        "17-Florence-X-Orchestration/Agent-Role-Map.md",
        "17-Florence-X-Orchestration/Handoff-Contract.md",
        "17-Florence-X-Orchestration/Interaction-Fields-Checklist.md",
        "17-Florence-X-Orchestration/Human-Orchestrator-Review.md",
        "17-Florence-X-Orchestration/Dry-Run-Orchestration-Plan.md",
        "17-Florence-X-Orchestration/Stop-and-Escalation-Rules.md",
        "17-Florence-X-Orchestration/Trace-Ledger.md",
        "17-Florence-X-Orchestration/Non-Deployment-Statement.md",
        "18-Governance-Board/README.md",
        "18-Governance-Board/Governance-Board-Charter.md",
        "18-Governance-Board/Steward-Council-Overview.md",
        "18-Governance-Board/Member-Role-Card.md",
        "18-Governance-Board/Review-Intake-Form.md",
        "18-Governance-Board/Agenda-Template.md",
        "18-Governance-Board/Decision-Record.md",
        "18-Governance-Board/Conflict-of-Interest-Disclosure.md",
        "18-Governance-Board/Boundary-and-Scope-Statement.md",
        "18-Governance-Board/Escalation-and-Referral-Path.md",
        "18-Governance-Board/Voting-and-Quorum-Checklist.md",
        "18-Governance-Board/Transparency-Ledger.md",
        "18-Governance-Board/Non-Authority-Statement.md",
        "19-Partner-Briefing/README.md",
        "19-Partner-Briefing/Partner-Briefing-Overview.md",
        "19-Partner-Briefing/One-Page-Partner-Brief.md",
        "19-Partner-Briefing/Use-Case-Boundary-Map.md",
        "19-Partner-Briefing/Stakeholder-Question-Prep.md",
        "19-Partner-Briefing/Claim-vs-Proof-Ledger.md",
        "19-Partner-Briefing/Demo-Boundary-Script.md",
        "19-Partner-Briefing/Partner-Intake-Form.md",
        "19-Partner-Briefing/Risk-and-Referral-Notes.md",
        "19-Partner-Briefing/Sponsor-Conversation-Guide.md",
        "19-Partner-Briefing/Non-Solicitation-and-Non-Approval-Statement.md",
        "19-Partner-Briefing/Follow-Up-Decision-Record.md",
        "20-Stewardship-Operating-Model/README.md",
        "20-Stewardship-Operating-Model/Operating-Model-Overview.md",
        "20-Stewardship-Operating-Model/Role-and-Cadence-Map.md",
        "20-Stewardship-Operating-Model/Intake-to-Decision-Workflow.md",
        "20-Stewardship-Operating-Model/Human-Gate-RACI.md",
        "20-Stewardship-Operating-Model/Stewardship-Meeting-Agenda.md",
        "20-Stewardship-Operating-Model/Risk-Escalation-Map.md",
        "20-Stewardship-Operating-Model/Stewardship-Metrics-Scorecard.md",
        "20-Stewardship-Operating-Model/Implementation-Backlog-Template.md",
        "20-Stewardship-Operating-Model/Adoption-Readiness-Conversation-Guide.md",
        "20-Stewardship-Operating-Model/Non-Authority-and-No-Deployment-Statement.md",
        "20-Stewardship-Operating-Model/Quarterly-Stewardship-Review.md",
        "21-Localization-Readiness/README.md",
        "21-Localization-Readiness/Localization-Readiness-Overview.md",
        "21-Localization-Readiness/Region-and-Audience-Map.md",
        "21-Localization-Readiness/Language-and-Tone-Adaptation-Guide.md",
        "21-Localization-Readiness/Jurisdiction-Boundary-Checklist.md",
        "21-Localization-Readiness/Cultural-Stewardship-Interview.md",
        "21-Localization-Readiness/Local-Partner-Question-Prep.md",
        "21-Localization-Readiness/Claim-vs-Local-Proof-Ledger.md",
        "21-Localization-Readiness/Translation-Review-Workflow.md",
        "21-Localization-Readiness/Cross-Border-Data-and-Privacy-Notes.md",
        "21-Localization-Readiness/Non-Authority-and-No-Localization-Approval-Statement.md",
        "21-Localization-Readiness/Localization-Decision-Record.md",
        "22-Adoption-Outcomes-Ledger/README.md",
        "22-Adoption-Outcomes-Ledger/Adoption-Ledger-Overview.md",
        "22-Adoption-Outcomes-Ledger/Safe-Use-Metrics-Map.md",
        "22-Adoption-Outcomes-Ledger/Time-Saved-Estimate-Worksheet.md",
        "22-Adoption-Outcomes-Ledger/Human-Gate-Pattern-Log.md",
        "22-Adoption-Outcomes-Ledger/Friction-and-Risk-Register.md",
        "22-Adoption-Outcomes-Ledger/Nurse-Confidence-Pulse.md",
        "22-Adoption-Outcomes-Ledger/Workflow-Before-After-Capture.md",
        "22-Adoption-Outcomes-Ledger/Learning-Milestone-Ledger.md",
        "22-Adoption-Outcomes-Ledger/Cohort-Adoption-Summary.md",
        "22-Adoption-Outcomes-Ledger/Institutional-Signal-Brief.md",
        "22-Adoption-Outcomes-Ledger/Non-Clinical-Outcome-and-No-Efficacy-Claim-Statement.md",
        "22-Adoption-Outcomes-Ledger/Adoption-Decision-Record.md",
        "23-Commercial-Activation/README.md",
        "23-Commercial-Activation/Founding-Steward-Cohort-Offer.md",
        "23-Commercial-Activation/Application-CTA-and-Form-Copy.md",
        "23-Commercial-Activation/Launch-Conversion-Path.md",
        "23-Commercial-Activation/Pilot-Conversation-Deck-Guide.md",
        "23-Commercial-Activation/Pilot-Charter-One-Pager.md",
        "23-Commercial-Activation/Warm-Invite-and-Follow-Up-Emails.md",
        "23-Commercial-Activation/Cohort-Seat-and-Scholarship-Policy.md",
        "23-Commercial-Activation/Manual-Review-Decision-Record.md",
        "23-Commercial-Activation/Claim-Boundary-and-No-Authority-Statement.md",
        "23-Commercial-Activation/Commercial-Activation-Decision-Record.md",
    ]
    for rel in expected:
        check(f"generated {rel}", (target / rel).is_file())

    if yaml is None:
        fail("pyyaml unavailable; cannot inspect rendered runtime")
        return
    runtime = yaml.safe_load((target / "config/edena-runtime.yaml").read_text(encoding="utf-8"))
    rituals = yaml.safe_load((target / "cron/rituals.yaml").read_text(encoding="utf-8"))
    combined = "\n".join(p.read_text(errors="ignore") for p in target.rglob("*") if p.is_file())

    check("runtime version phase23", runtime.get("version") == "2.0.0-phase23")
    check("runtime includes 5 skills", len(runtime.get("skills", [])) == 5)
    check("runtime includes 4 cron rituals", len(runtime.get("cron_rituals", [])) == 4)
    check("cron rituals are templates only", rituals.get("mode") == "templates_only_not_scheduled")
    check("cron rituals remain unscheduled", all(x.get("scheduled") is False for x in runtime.get("cron_rituals", [])))
    check("skills are EDENA tier-tagged", combined.count("edena_tier:") >= 5)
    check("Green and Yellow gates are present", "human_gate: every-output" in combined and "human_gate: before-external-use" in combined)
    check("no-PHI boundary is carried", "Do not request or infer patient information" in combined)
    check("doctrine is carried", "Agents propose. Humans judge. Nurses steward." in combined)
    check("START-HERE carries first safe prompts", "Your first 3 safe prompts" in combined and "Open START-HERE.md" in combined)
    check("first-week activation path is present", "Day 1 — Setup and Safety" in combined and "Day 7 — Weekly Ledger" in combined)
    check("public launch pack is present", "Phase 18 Public Launch Pack" in combined and "Launch Checklist" in combined and "not clinical decision support" in combined)
    check("cohort mode pack is present", "Phase 18 Cohort Mode" in combined and "Participant Readiness Rubric" in combined and "not certification" in combined)
    check("evidence trail pack is present", "Phase 18 EDENA Evidence Trail" in combined and "Evidence Capture Guide" in combined and "Not Certification Statement" in combined and "no automatic scoring" in combined.lower())
    check("contribution flow pack is present", "Phase 18 NIN Community Contribution Flow" in combined and "Contribution Intake Guide" in combined and "Not Endorsement Statement" in combined and "no automatic publishing" in combined.lower())
    check("institutional pilot pack is present", "Phase 18 Institutional Pilot Pack" in combined and "Pilot Charter" in combined and "Not Clinical Deployment Statement" in combined and "no automatic reporting" in combined.lower())
    check("EDENA readiness pack is present", "Phase 18 EDENA Micro-Credential Readiness Pack" in combined and "Readiness Overview" in combined and "Non-Certification Statement" in combined and "no automatic scoring" in combined.lower())
    check("agent registry pack is present", "Phase 18 NAIO Agent Registry Pack" in combined and "Agent Intake Card" in combined and "Not-Endorsement Statement" in combined and "no automatic listing" in combined.lower())
    check("Florence-X orchestration pack is present", "Phase 18 Florence-X Orchestration Preview Pack" in combined and "Shared Intent Card" in combined and "Non-Deployment Statement" in combined and "no automatic handoffs" in combined.lower())
    check("governance board pack is present", "Phase 18 Governance Board / Steward Council Pack" in combined and "Governance Board Charter" in combined and "Non-Authority Statement" in combined and "no automatic approvals" in combined.lower())
    check("partner briefing pack is present", "Phase 19 Partner / Sponsor Briefing Pack" in combined and "One-Page Partner Brief" in combined and "Non-Solicitation and Non-Approval Statement" in combined and "no automatic outreach" in combined.lower())
    check("stewardship operating model pack is present", "Phase 20 Institutional Stewardship Operating Model Pack" in combined and "Human-Gate RACI" in combined and "Non-Authority and No-Deployment Statement" in combined and "no automatic implementation" in combined.lower())
    check("localization readiness pack is present", "Phase 21 Localization / International Readiness Lane Pack" in combined and "Region and Audience Map" in combined and "Non-Authority and No-Localization-Approval Statement" in combined and "no automatic translation" in combined.lower())
    check("outcomes ledger pack is present", "Phase 22 Adoption & Outcomes Ledger Pack" in combined and "Adoption Ledger Overview" in combined and "Non-Clinical Outcome and No-Efficacy-Claim Statement" in combined and "no automatic dashboard" in combined.lower())

    check("commercial activation pack is present", "Phase 23 Commercial Activation Pack" in combined and "Founding Steward Cohort Offer" in combined and "Pilot Charter One-Pager" in combined and "Payment link only after human acceptance" in combined and "No automatic enrollment" in combined)


def main() -> int:
    parser = argparse.ArgumentParser(description="NAIO OS Phase 23 self-test harness")
    parser.add_argument("--keep-target", action="store_true", help="do not delete the generated temporary target")
    args = parser.parse_args()

    print("\n=== NAIO OS — Phase 23 self-test ===\n")
    print("This is an ad-hoc smoke test for the downloadable bundle, not canonical suite green.\n")

    hc = run(["python3", "scripts/healthcheck.py"])
    check("full healthcheck exits 0", hc.returncode == 0, f"exit={hc.returncode}")

    update = run(["python3", "scripts/check-update.py", "--local-only", "--json"])
    check("local update advisory verifies rollback protection", update.returncode == 0 and '"rollback_protected": true' in update.stdout and '"no_mutation": true' in update.stdout, f"exit={update.returncode}")

    tmp = Path(tempfile.mkdtemp(prefix="naio-os-self-test-"))
    target = tmp / "NAIO-Hermes-Profile"
    try:
        soul_path = tmp / "naio-soul.json"
        projects_path = tmp / "naio-projects.json"
        soul_path.write_text(json.dumps(sample_soul()), encoding="utf-8")
        projects_path.write_text(json.dumps(sample_projects()), encoding="utf-8")

        dry = run(["bash", "install.sh", "--dry-run", "--soul", str(soul_path), "--projects", str(projects_path)])
        check("dry-run validates imports and writes nothing", dry.returncode == 0 and "Nothing written" in (dry.stdout + dry.stderr), f"exit={dry.returncode}")

        applied = run(["bash", "install.sh", "--apply", "--soul", str(soul_path), "--projects", str(projects_path), "--target", str(target)])
        check("target-only apply exits 0", applied.returncode == 0, f"exit={applied.returncode}")
        if target.exists():
            verify_target(target)
            recovery = run(["python3", "scripts/recovery.py", "--drill", "--profile", str(target)])
            check("recovery drill snapshots/verifies/extracts/plans with no mutation", recovery.returncode == 0 and '"status": "drill-passed"' in recovery.stdout and '"no_mutation": true' in recovery.stdout, f"exit={recovery.returncode}")
            activation = run(["python3", "scripts/activation.py", "--profile", str(target), "--json"])
            check("activation check reports ready and no mutation", activation.returncode == 0 and '"status": "ready"' in activation.stdout and '"safe_to_start": true' in activation.stdout and '"no_mutation": true' in activation.stdout, f"exit={activation.returncode}")
            launch = run(["python3", "scripts/launch.py", "--profile", str(target), "--json"])
            check("launch check reports ready and no mutation", launch.returncode == 0 and '"status": "ready"' in launch.stdout and '"safe_to_share": true' in launch.stdout and '"no_mutation": true' in launch.stdout, f"exit={launch.returncode}")
            cohort = run(["python3", "scripts/cohort.py", "--profile", str(target), "--json"])
            check("cohort check reports ready and no mutation", cohort.returncode == 0 and '"status": "ready"' in cohort.stdout and '"cohort_ready": true' in cohort.stdout and '"safe_to_facilitate": true' in cohort.stdout and '"no_mutation": true' in cohort.stdout, f"exit={cohort.returncode}")
            evidence = run(["python3", "scripts/evidence.py", "--profile", str(target), "--json"])
            check("evidence check reports ready and no mutation", evidence.returncode == 0 and '"status": "ready"' in evidence.stdout and '"evidence_ready": true' in evidence.stdout and '"safe_to_document": true' in evidence.stdout and '"no_mutation": true' in evidence.stdout, f"exit={evidence.returncode}")
            contribution = run(["python3", "scripts/contribute.py", "--profile", str(target), "--json"])
            check("contribution check reports ready and no mutation", contribution.returncode == 0 and '"status": "ready"' in contribution.stdout and '"contribution_ready": true' in contribution.stdout and '"safe_to_contribute": true' in contribution.stdout and '"no_mutation": true' in contribution.stdout, f"exit={contribution.returncode}")
            pilot = run(["python3", "scripts/pilot.py", "--profile", str(target), "--json"])
            check("pilot check reports ready and no mutation", pilot.returncode == 0 and '"status": "ready"' in pilot.stdout and '"pilot_ready": true' in pilot.stdout and '"safe_to_pilot": true' in pilot.stdout and '"no_mutation": true' in pilot.stdout, f"exit={pilot.returncode}")
            readiness = run(["python3", "scripts/readiness.py", "--profile", str(target), "--json"])
            check("readiness check reports ready and no mutation", readiness.returncode == 0 and '"status": "ready"' in readiness.stdout and '"readiness_ready": true' in readiness.stdout and '"safe_to_review": true' in readiness.stdout and '"no_mutation": true' in readiness.stdout, f"exit={readiness.returncode}")
            registry = run(["python3", "scripts/registry.py", "--profile", str(target), "--json"])
            check("registry check reports ready and no mutation", registry.returncode == 0 and '"status": "ready"' in registry.stdout and '"registry_ready": true' in registry.stdout and '"safe_to_list": true' in registry.stdout and '"no_mutation": true' in registry.stdout, f"exit={registry.returncode}")
            orchestration = run(["python3", "scripts/orchestration.py", "--profile", str(target), "--json"])
            check("orchestration check reports ready and no mutation", orchestration.returncode == 0 and '"status": "ready"' in orchestration.stdout and '"orchestration_ready": true' in orchestration.stdout and '"safe_to_rehearse": true' in orchestration.stdout and '"no_mutation": true' in orchestration.stdout, f"exit={orchestration.returncode}")
            governance = run(["python3", "scripts/governance.py", "--profile", str(target), "--json"])
            check("governance check reports ready and no mutation", governance.returncode == 0 and '"status": "ready"' in governance.stdout and '"governance_ready": true' in governance.stdout and '"safe_to_convene": true' in governance.stdout and '"no_mutation": true' in governance.stdout, f"exit={governance.returncode}")
            partner = run(["python3", "scripts/partner.py", "--profile", str(target), "--json"])
            check("partner check reports ready and no mutation", partner.returncode == 0 and '"status": "ready"' in partner.stdout and '"partner_ready": true' in partner.stdout and '"safe_to_brief": true' in partner.stdout and '"no_mutation": true' in partner.stdout, f"exit={partner.returncode}")
            stewardship = run(["python3", "scripts/stewardship.py", "--profile", str(target), "--json"])
            check("stewardship check reports ready and no mutation", stewardship.returncode == 0 and '"status": "ready"' in stewardship.stdout and '"stewardship_ready": true' in stewardship.stdout and '"safe_to_coordinate": true' in stewardship.stdout and '"no_mutation": true' in stewardship.stdout, f"exit={stewardship.returncode}")
            localization = run(["python3", "scripts/localization.py", "--profile", str(target), "--json"])
            check("localization check reports ready and no mutation", localization.returncode == 0 and '"status": "ready"' in localization.stdout and '"localization_ready": true' in localization.stdout and '"safe_to_localize": true' in localization.stdout and '"no_mutation": true' in localization.stdout, f"exit={localization.returncode}")
            outcomes = run(["python3", "scripts/outcomes.py", "--profile", str(target), "--json"])
            check("outcomes check reports ready and no mutation", outcomes.returncode == 0 and '"status": "ready"' in outcomes.stdout and '"outcomes_ready": true' in outcomes.stdout and '"safe_to_measure": true' in outcomes.stdout and '"no_mutation": true' in outcomes.stdout, f"exit={outcomes.returncode}")
            commercial = run(["python3", "scripts/commercial.py", "--profile", str(target), "--json"])
            check("commercial check reports ready and no mutation", commercial.returncode == 0 and '"status": "ready"' in commercial.stdout and '"commercial_ready": true' in commercial.stdout and '"safe_to_activate": true' in commercial.stdout and '"no_mutation": true' in commercial.stdout, f"exit={commercial.returncode}")
        else:
            fail("target directory was not created")

        refuses_home = run(["python3", "scripts/render-profile.py", "--soul", str(soul_path), "--target", str(Path.home() / ".hermes"), "--force"])
        check("renderer refuses direct ~/.hermes overwrite", refuses_home.returncode == 2, f"exit={refuses_home.returncode}")

        orange = sample_soul()
        orange["tier_ceilings"] = {"professional": "orange"}
        orange_path = tmp / "bad-orange.json"
        orange_path.write_text(json.dumps(orange), encoding="utf-8")
        refuses_orange = run(["bash", "install.sh", "--apply", "--soul", str(orange_path), "--target", str(tmp / "bad-target")])
        check("installer refuses Orange onboarding tier", refuses_orange.returncode == 2, f"exit={refuses_orange.returncode}")
    finally:
        if args.keep_target:
            print(f"\nTemporary self-test directory kept: {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)

    print("\n--- self-test summary ---")
    print(f"  ok:   {PASS}")
    print(f"  fail: {FAIL}")
    if FAIL:
        print("\n❌ SELF-TEST FAILED — do not apply this bundle yet.")
    else:
        print("\n✅ SELF-TEST PASSED — bundle behavior is consistent with Phase 23 safety contract.")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
