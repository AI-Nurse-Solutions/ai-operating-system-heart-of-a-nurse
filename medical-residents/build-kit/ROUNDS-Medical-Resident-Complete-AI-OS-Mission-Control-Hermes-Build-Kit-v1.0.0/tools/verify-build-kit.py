#!/usr/bin/env python3
"""Verify the Medical Resident Complete AI OS with ROUNDS Hermes build kit.

Passing this verifier establishes build-kit integrity only. It never establishes
that the target application, Hermes integration, professional authority, or a
clinical/institutional deployment is operational.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import stat
import sys
import unicodedata
import uuid
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any


PACKAGE_NAME = "ROUNDS-Medical-Resident-Complete-AI-OS-Mission-Control-Hermes-Build-Kit-v1.0.0"
ZIP_ALIAS_NAME = "ROUNDS-Medical-Resident-Complete-AI-OS-Mission-Control-Hermes-Build-Kit.zip"
BUILD_ID = "NAIO-MR-ROUNDS-FUNCTIONAL-BUILD-KIT-1.0.0"
PRODUCT = "ROUNDS — Medical Resident Complete AI OS Mission Control"
PRODUCT_ID = "medical-resident-rounds-mission-control"
LANE = "medical_resident"
ROUTE = "/medical-residents"
FOUNDATION_NAMESPACE = "medres_rounds.*"
NAMESPACE = "medres_rounds.*"
HOME = "My ROUNDS"

PROMPT_SHA = "ce884cfc6345cc93a6baec0852cf44feb44d859234ef1dc2b5ac2138df18ebe2"
BASELINE_ZIP_SHA = "69a4dd86659b41136ce9ceb2ceb52512ab567637ab0be29fdc6f6ab6573223c1"
BASELINE_MANIFEST_SHA = "22fed55fd789c933f4e7eb50266f88f8dda47f9fba91ebbe9c2cbe4f0ab99702"
BASELINE_CHECKSUMS_SHA = "e178993d6185b126cc915f0d3026ddb3b07e7c5c7dd432aaf581152db8a5a40e"
COMPLETE_PROGRAM_SHA = "63524f871de3a28842d04e936b7bce7bd2b3a76724f08222179a7a8c7365d35e"
COMPLETE_SETUP_MD_SHA = "5afbd0e56253167d6fe4247aaa081b520d648a232af98e212c0f2a355d2e4ead"
COMPLETE_SETUP_DOCX_SHA = "a0c4483ca3b51d0597db52b8c32c5dcc93e9916ae2374277b1962f1832f50d4b"
LEGACY_COMPLETE_ZIP_SHA = "29143447f94aff0034c96019ff83a29370cbb17a1448c68d191a2354a847ce26"
ROUNDS_TREE_DIGEST = "6b38342ffc14d13f6693d7fefb4f52f258471328cc76ca7226b382a4e7e47683"
COMPLETE_TREE_DIGEST = "4fa7a3bacfa50305fe425e5ba4d06c7da6c0894215b0f6bea3f265a77e53fbbb"

ROUNDS_TREE_HASHES = {
    "README.md": "d8b4deb264ca3e595fcec28994b4730a3a44bcaebf09fd8c0db89683fe7d5297",
    "core/00-Standalone-Medical-Resident-Lane-and-Human-Standard.md": "6141c678cf15ea4a7d3c8bf78848e7a97cb66c698074f989bc26dcf71d4efbd9",
    "core/01-Resident-Patient-Training-and-Institution-Trust-Shield.md": "0eb3a048b0f2ab54da36f903306f666caaed7f49e372ec87b501f128037eb0a7",
    "core/02-ROUNDS-ATTEND-CIRCLE-ORBIT-Operating-Core.md": "bfc4a7854988564e5719bff045cb8027335c814ff22c3db1f20df28889ad6cef",
    "foundation/Medical-Resident-Life-Training-and-Practice-Foundation.md": "ee80baf4178aaa6300f20dec013356c314bafd67ac71d8c8e1ab8b4df2d5d021",
    "manifest.md": "137431155158be3b9c426c396841782dc316fafa4895651c041a7c474f41d072",
    "rounds/01-R-Ready-the-Resident-and-Protect-Life.md": "54932bee6b48dbd264d6c14bc02649367bec0fbb35ac1acb261c937b31ae948f",
    "rounds/02-O-Orchestrate-Care-Teams-and-Transitions.md": "177654d46580f858d693abd1b23c4acc52dee9ae76e37b4f321e1f47e6ce3ebd",
    "rounds/03-U-Understand-Evidence-Reasoning-and-Systems.md": "88114a1a252ea97f7c348ea401bfa258a284d71878b28a1bcb62d9406648ba15",
    "rounds/04-N-Navigate-Supervision-Development-and-Career.md": "cde6e9e8620bc87c5a81fb81863dd61daa5609f3c1eca4022dc97681723987e9",
    "rounds/05-D-Develop-Communication-Teaching-Scholarship-and-Leadership.md": "17226738d301a7ff30489f991f7e137ff80b7be3618de454124a39b9cd81d4fb",
    "rounds/06-S-Steward-AI-Agents-Data-and-the-Future.md": "46352e2e47fca286b5dcf42ffaf7f04f94c7bac723ab1e063d4a5cb828dc4ec7",
    "templates/ROUNDS-Cards-and-Templates.md": "76de090543e1bdb9f2e24567f2db0dae422573ab217df0d197e00483deaeb0fe",
    "tests/ROUNDS-Release-Assurance.md": "3da9df6087b43712eebe0c86a26ebc160c45ba72882f5925ed90f98062dbdce0",
    "workflows/My-ROUNDS-Resident-Command-Center.md": "5bf5779e4db2ffc306b8a39c8dc183ef18393a560a7f3977cd31cc7e044c065a",
    "workflows/ROUNDS-Workflows-Launch-and-Adoption-Plan.md": "1e6d6bec4c46e8d182990eefad2c6a95299d149a2beb20da082b91bd8b447e14",
    "workflows/Resident-Role-Rotation-and-Situation-Recipes.md": "28caf0c65e584a985091f0f07a960bff387a90b4835a488cde1d79c6807b4264",
}

COMPLETE_TREE_HASHES = {
    "README.md": "bf1e43b8d70772cd4e68dcdcd3e8b906ebd7a342def60ef192494bef8edbc720",
    **{f"Medical-Resident-ROUNDS-SuperPowers-Pack-v1.0/{name}": digest for name, digest in ROUNDS_TREE_HASHES.items()},
    "Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Hermes-Program.md": COMPLETE_PROGRAM_SHA,
    "Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Setup-Guide.docx": COMPLETE_SETUP_DOCX_SHA,
    "Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Setup-Guide.md": COMPLETE_SETUP_MD_SHA,
    "SHA256SUMS.txt": "12b7b8f5f6e8498442a4a40c41fc5a993fc51c5e91b39d62636ff7cf214bad28",
}

CORE_FOUR = ["Orient My Day & Duty", "Learn & Reason", "Orchestrate & Communicate", "Review, Escalate & Close"]
POWERS = [
    "Rotation & Call Readiness Navigator",
    "Duty-Hours, Fatigue & Safe-Transport Shield",
    "Capacity, Leave, Recovery & Human-Support Navigator",
    "Mission, Finances, Family & Future Compass",
    "Supervision-Aware Care Orchestration Mapper",
    "Consult, Interdisciplinary Team & Closed-Loop Coordination Studio",
    "Handoff, Cross-Cover & Transition Reliability Rehearsal",
    "Follow-Up, Barrier & Contingency Reliability Planner",
    "Evidence, Guideline & Uncertainty Navigator",
    "Synthetic Clinical Reasoning & Diagnostic Calibration Lab",
    "Journal Club, Adaptive Learning & Knowledge Synthesis Studio",
    "Quality, Patient Safety & Implementation Lab",
    "Graduated Responsibility, Supervision & Escalation Compass",
    "Milestones, EPAs, Feedback & Development Map",
    "License, Exam, Procedure Authorization & Credential Radar",
    "Fellowship, Career, Contract & Opportunity Navigator",
    "Human Communication, Consent & Difficult-Conversation Rehearsal",
    "Teaching, Bedside Education & Case-Conference Studio",
    "Research, Scholarship, Authorship & Professional Voice Forge",
    "Feedback, Conflict, Mistreatment & Psychological-Safety Navigator",
    "AI Agent Charter, Tool, Permission & Data Registry",
    "Multi-Agent Orchestration & Human-Handoff Designer",
    "Agent Output, Source, Bias, Security & Trace Auditor",
    "Agent Incident, Pause, Failover, Rollback & Retirement Controller",
]
WORKFLOWS = [
    "Resident Whole-Day or Call Orientation", "Weekly Rotation & Whole-Life Reset",
    "Duty-Hour & Schedule Reality Review", "Post-Call Recovery, Relief & Safe-Commute Plan",
    "Rotation or Site Onboarding", "General Evidence or Guideline Brief",
    "Synthetic Case Reasoning & Cognitive-Bias Simulation", "Procedure or Skill Deliberate-Practice Plan",
    "CIRCLE Rounds or Care-Orchestration Rehearsal", "Handoff & Cross-Cover Reliability Preparation",
    "Consult Question, Request, Response & Follow-Up Brief", "Transition, Disposition & Follow-Up Coordination Brief",
    "Attending Escalation, Advocacy or Difficult-Conversation Prep", "Feedback, Debrief & Milestone Self-Evidence Review",
    "CCC Self-Reflection & Questions Packet", "In-Training or Board Exam, License & Credential Plan",
    "Teaching, Bedside Education or Conference Build", "Patient-Safety Event or M&M Preparation",
    "Quality, PDSA & Systems-Improvement Project", "Research, IRB, Methods & Manuscript Project",
    "Fellowship, Job, Portfolio & Interview Pathway", "Contract, Benefits, Debt & Financial Decision Brief",
    "Family, Health, Relationships, Purpose & Minimum Mode", "ORBIT Agent Preview, Synthetic Test, One-Run Receipt & Termination",
]
TEMPLATES = [
    "Resident ROUNDS True North & Protected-Life Promise", "Active Hat, Program, Site, Rotation & Decision-Rights Card",
    "Graduated Responsibility & Supervision Matrix", "ATTEND Gate Receipt", "Daily or Call Orientation Card",
    "Duty-Hour, Call, Moonlighting & Recovery Reality Log", "Fatigue Relief, Safe-Commute & Support Plan",
    "Rotation or Site Onboarding & Escalation Map", "CIRCLE Care-Orchestration Map",
    "Handoff or Cross-Cover Closed-Loop Card", "Consult Question, Contact, Acknowledgment & Follow-Up Card",
    "Transition, Disposition & Follow-Up Responsibility Map", "Evidence, Guideline & Source Brief",
    "Synthetic Clinical-Reasoning & Bias Reflection Sheet", "Procedure or Skill Deliberate-Practice Plan",
    "Attending, Program, Advocacy or Difficult-Conversation Brief", "Feedback & Milestone Self-Evidence Log",
    "CCC Self-Reflection & Questions Packet", "Exam, License, Credential & Procedure-Authorization Radar",
    "Teaching Session or Microteaching Brief", "Safety or M&M Reflection & Official-System Boundary Card",
    "Quality Charter, PDSA, Measure, Equity & Balance Record", "QI-versus-Research Human Determination Receipt",
    "Research, IRB, Data, Methods, Authorship & Release Plan", "Fellowship, Career, Portfolio & Evidence Map",
    "Contract, Benefits, Finance & Decision Questions Brief", "Whole-Life Capacity, Family, Purpose & Minimum-Mode Plan",
    "ORBIT Agent Definition & Permission Envelope", "Agent Preview, Test, Run, Review, Release & Termination Receipt",
    "Seven-Day Launch & Ninety-Day Development Plan",
]
WORKSPACES = [
    ("rounds-role-duty-life", "Role, Duty & Life"),
    ("rounds-learning-reasoning-evidence", "Learning, Reasoning & Evidence"),
    ("rounds-supervision-communication-orchestration", "Supervision, Communication & Orchestration"),
    ("rounds-development-quality-scholarship", "Development, Quality & Scholarship"),
    ("rounds-credentials-career-future", "Credentials, Career & Future"),
]
AGENTS = [
    ("AGT-01", "Day & Capacity Planner", "PERM-P1"),
    ("AGT-02", "Evidence Scout", "PERM-P2"),
    ("AGT-03", "Synthetic Case Coach", "PERM-P1"),
    ("AGT-04", "Source & Claim Verifier", "PERM-P2"),
    ("AGT-05", "Care-Orchestration Assistant", "PERM-P3"),
    ("AGT-06", "Handoff & Consult Draft Assistant", "PERM-P3"),
    ("AGT-07", "Quality Mapper", "PERM-P3"),
    ("AGT-08", "Research Steward", "PERM-P3"),
    ("AGT-09", "Teaching Builder", "PERM-P3"),
    ("AGT-10", "Career & Whole-Life Planner", "PERM-P2"),
]
AGENT_PERSONAL_CONTRACTS = {
    "AGT-01": {
        "personal_available": True, "personal_maximum": "PERM-P1",
        "allowed_modes": ["private_nonsensitive_one_run"],
        "allowed_data_classes": ["MR-DATA-1", "MR-DATA-2"],
        "allowed_outputs": ["private_capacity_plan", "recovery_questions", "minimum_mode_draft"],
        "router": "rounds-role-duty-life",
    },
    "AGT-02": {
        "personal_available": True, "personal_maximum": "PERM-P2",
        "allowed_modes": ["public_source_one_run", "approved_read_only_one_run"],
        "allowed_data_classes": ["MR-DATA-0", "MR-DATA-1", "MR-DATA-2"],
        "allowed_outputs": ["source_brief", "claim_source_map", "unresolved_conflict_list"],
        "router": "rounds-learning-reasoning-evidence",
    },
    "AGT-03": {
        "personal_available": True, "personal_maximum": "PERM-P1",
        "allowed_modes": ["synthetic_one_run"], "allowed_data_classes": ["MR-DATA-1"],
        "allowed_outputs": ["fictional_reasoning_feedback", "bias_reflection_questions"],
        "router": "rounds-learning-reasoning-evidence",
    },
    "AGT-04": {
        "personal_available": True, "personal_maximum": "PERM-P2",
        "allowed_modes": ["public_source_one_run", "approved_read_only_one_run"],
        "allowed_data_classes": ["MR-DATA-0", "MR-DATA-1", "MR-DATA-2"],
        "allowed_outputs": ["source_audit", "claim_verification_table", "uncertainty_register"],
        "router": "rounds-learning-reasoning-evidence",
    },
    "AGT-05": {
        "personal_available": False, "personal_maximum": "PERM-P0", "allowed_modes": [],
        "allowed_data_classes": [], "allowed_outputs": [], "router": "unavailable_personal_preview_only",
    },
    "AGT-06": {
        "personal_available": False, "personal_maximum": "PERM-P0", "allowed_modes": [],
        "allowed_data_classes": [], "allowed_outputs": [], "router": "unavailable_personal_preview_only",
    },
    "AGT-07": {
        "personal_available": True, "personal_maximum": "PERM-P1",
        "allowed_modes": ["synthetic_one_run", "public_source_one_run"],
        "allowed_data_classes": ["MR-DATA-0", "MR-DATA-1"],
        "allowed_outputs": ["synthetic_quality_map", "human_determination_questions"],
        "router": "rounds-development-quality-scholarship",
    },
    "AGT-08": {
        "personal_available": True, "personal_maximum": "PERM-P1",
        "allowed_modes": ["synthetic_one_run", "public_source_one_run"],
        "allowed_data_classes": ["MR-DATA-0", "MR-DATA-1"],
        "allowed_outputs": ["synthetic_protocol_outline", "human_research_determination_questions"],
        "router": "rounds-development-quality-scholarship",
    },
    "AGT-09": {
        "personal_available": True, "personal_maximum": "PERM-P1",
        "allowed_modes": ["synthetic_one_run", "public_source_one_run"],
        "allowed_data_classes": ["MR-DATA-0", "MR-DATA-1"],
        "allowed_outputs": ["synthetic_teaching_draft", "accessibility_and_copyright_checklist"],
        "router": "rounds-development-quality-scholarship",
    },
    "AGT-10": {
        "personal_available": True, "personal_maximum": "PERM-P2",
        "allowed_modes": ["private_nonsensitive_one_run", "approved_read_only_one_run"],
        "allowed_data_classes": ["MR-DATA-0", "MR-DATA-1", "MR-DATA-2"],
        "allowed_outputs": ["private_decision_questions", "career_option_brief", "nonsensitive_whole_life_questions"],
        "router": "rounds-credentials-career-future",
    },
}
TASK_HATS = [
    "clinical_team_member", "cross_cover_or_on_call", "senior_or_team_lead",
    "chief_clinical", "chief_administrative", "educator",
    "quality_or_patient_safety_contributor", "researcher_or_scholar",
    "learner_or_exam_candidate", "fellowship_or_career_applicant", "personal_private",
]
PARTITIONS = [
    "resident_private", "whole_life_private", "synthetic_learning", "institution_clinical",
    "institution_education", "institution_quality_safety", "institution_research", "institution_program_gme",
    "institution_agent",
]
PRIVATE_PARTITIONS = PARTITIONS[:3]
INSTITUTIONAL_PARTITIONS = PARTITIONS[3:]
ROLE_STATUSES = [
    "intern_or_early_resident", "advancing_resident", "senior_or_team_lead_resident",
    "chief_resident", "off_service_visiting_or_cross_cover_resident",
    "unknown_stale_expired_or_conflicting",
]
ROLE_ADAPTERS = ROLE_STATUSES[:-1]
RECORD_SCHEMAS = [
    "resident_profile", "active_hat_context", "supervision_matrix_entry", "duty_and_recovery_cycle",
    "source_record", "learning_plan", "synthetic_reasoning_record", "circle_orchestration_record",
    "handoff_or_consult_receipt", "feedback_milestone_evidence", "credential_exam_radar",
    "qi_or_research_project", "teaching_scholarship_record", "career_whole_life_goal",
    "agent_definition", "agent_run_receipt", "human_approval_receipt",
]
RECORD_CONTRACT_EXPECTATIONS = {
    "resident_profile": (
        ["rounds-role-duty-life"], ["resident_private"], ["MR-DATA-2", "MR-DATA-M", "MR-DATA-R"],
        "foundation/Medical-Resident-Life-Training-and-Practice-Foundation.md",
        ["raw_soul_raw_discover_raw_quiz_or_unreviewed_profile_payload", "third_party_identity_story_or_contact_graph"],
        ["infer_role_hat_specialty_pgy_site_or_supervision", "share_profile_or_use_it_to_unlock_another_context"],
    ),
    "active_hat_context": (
        ["rounds-supervision-communication-orchestration"], ["resident_private"], ["MR-DATA-2", "MR-DATA-M", "MR-DATA-R"],
        "core/00-Standalone-Medical-Resident-Lane-and-Human-Standard.md",
        ["patient_assignment_or_live_service_task", "formal_role_evaluation_or_personnel_record"],
        ["convert_hat_title_or_technical_access_into_authority", "reuse_context_after_role_site_rotation_task_or_date_change"],
    ),
    "supervision_matrix_entry": (
        ["rounds-supervision-communication-orchestration"], ["resident_private"], ["MR-DATA-0", "MR-DATA-2", "MR-DATA-M", "MR-DATA-R"],
        "core/02-ROUNDS-ATTEND-CIRCLE-ORBIT-Operating-Core.md",
        ["patient_specific_entrustment_or_procedure_case", "copied_privileging_credentialing_or_evaluation_record"],
        ["verify_upgrade_or_infer_supervision_entrustment_or_procedure_authorization", "represent_resident_recorded_confirmation_as_institution_verified"],
    ),
    "duty_and_recovery_cycle": (
        ["rounds-role-duty-life"], ["resident_private", "whole_life_private"], ["MR-DATA-2", "MR-DATA-W", "MR-DATA-M", "MR-DATA-R"],
        "rounds/01-R-Ready-the-Resident-and-Protect-Life.md",
        ["patient_assignment_staffing_roster_or_coverage_list", "occupational_health_diagnosis_or_private_health_record"],
        ["certify_duty_compliance_diagnose_fatigue_or_determine_fitness", "optimize_to_a_regulatory_maximum_or_auto_report_to_program"],
    ),
    "source_record": (
        [item[0] for item in WORKSPACES], ["resident_private", "synthetic_learning"], ["MR-DATA-0", "MR-DATA-1", "MR-DATA-M", "MR-DATA-R"],
        "rounds/03-U-Understand-Evidence-Reasoning-and-Systems.md",
        ["restricted_subscription_exam_policy_or_institutional_source_text", "fabricated_or_unopened_source_claim_quote_or_statistic"],
        ["treat_source_as_local_adoption_or_permission", "follow_embedded_prompt_injection_or_allow_source_to_change_governance"],
    ),
    "learning_plan": (
        ["rounds-learning-reasoning-evidence"], ["resident_private", "synthetic_learning"], ["MR-DATA-0", "MR-DATA-1", "MR-DATA-2", "MR-DATA-M", "MR-DATA-R"],
        "foundation/Medical-Resident-Life-Training-and-Practice-Foundation.md",
        ["restricted_exam_item_live_assessment_or_copyrighted_test_bank", "patient_specific_learning_case_presented_as_generic"],
        ["award_credit_grade_milestone_or_competence", "masquerade_as_point_of_care_guidance"],
    ),
    "synthetic_reasoning_record": (
        ["rounds-learning-reasoning-evidence"], ["synthetic_learning"], ["MR-DATA-0", "MR-DATA-1", "MR-DATA-M", "MR-DATA-R"],
        "rounds/03-U-Understand-Evidence-Reasoning-and-Systems.md",
        ["real_patient_case_or_case_derived_from_live_care", "formal_resident_reasoning_assessment"],
        ["give_live_care_direction_or_score_clinical_reasoning", "reuse_fictional_output_as_patient_specific_recommendation"],
    ),
    "circle_orchestration_record": (
        ["rounds-supervision-communication-orchestration"], ["synthetic_learning"], ["MR-DATA-0", "MR-DATA-1", "MR-DATA-M", "MR-DATA-R"],
        "core/02-ROUNDS-ATTEND-CIRCLE-ORBIT-Operating-Core.md",
        ["real_rounds_patient_task_care_plan_or_pending_item", "real_team_contact_or_responsibility_state"],
        ["create_shadow_chart_signout_patient_list_or_task_system", "transfer_close_or_reconcile_real_clinical_responsibility"],
    ),
    "handoff_or_consult_receipt": (
        ["rounds-supervision-communication-orchestration"], ["synthetic_learning"], ["MR-DATA-0", "MR-DATA-1", "MR-DATA-M", "MR-DATA-R"],
        "rounds/02-O-Orchestrate-Care-Teams-and-Transitions.md",
        ["real_handoff_consult_cross_cover_or_transition_content", "real_sender_receiver_patient_or_acknowledgment"],
        ["contact_page_consult_or_message_anyone", "claim_acknowledgment_acceptance_closed_loop_or_transfer_of_responsibility"],
    ),
    "feedback_milestone_evidence": (
        ["rounds-development-quality-scholarship"], ["resident_private"], ["MR-DATA-2", "MR-DATA-M", "MR-DATA-R"],
        "rounds/04-N-Navigate-Supervision-Development-and-Career.md",
        ["formal_evaluation_raw_feedback_ccc_minutes_or_remediation_record", "identifiable_faculty_peer_learner_or_patient_story"],
        ["score_predict_rank_or_label_milestone_professionalism_or_progression", "export_private_reflection_to_program_employer_or_badge"],
    ),
    "credential_exam_radar": (
        ["rounds-credentials-career-future"], ["resident_private"], ["MR-DATA-0", "MR-DATA-2", "MR-DATA-M", "MR-DATA-R"],
        "rounds/04-N-Navigate-Supervision-Development-and-Career.md",
        ["license_number_npi_dea_login_signature_or_verification_secret", "restricted_exam_item_case_log_or_privileging_record"],
        ["certify_eligibility_license_credit_score_privilege_or_procedure_authorization", "backfill_submit_or_fabricate_log_application_or_evidence"],
    ),
    "qi_or_research_project": (
        ["rounds-development-quality-scholarship"], ["synthetic_learning"], ["MR-DATA-0", "MR-DATA-1", "MR-DATA-M", "MR-DATA-R"],
        "rounds/03-U-Understand-Evidence-Reasoning-and-Systems.md",
        ["real_event_m_and_m_peer_review_patient_project_or_research_data", "real_protocol_consent_irb_quality_or_sponsor_record"],
        ["determine_qi_research_exempt_or_irb_status", "launch_pilot_change_study_analysis_submission_publication_or_release"],
    ),
    "teaching_scholarship_record": (
        ["rounds-development-quality-scholarship"], ["resident_private", "synthetic_learning"], ["MR-DATA-0", "MR-DATA-1", "MR-DATA-2", "MR-DATA-M", "MR-DATA-R"],
        "rounds/05-D-Develop-Communication-Teaching-Scholarship-and-Leadership.md",
        ["identifiable_case_learner_submission_grade_or_secure_assessment", "restricted_copyrighted_material_unapproved_data_or_hidden_authorship"],
        ["grade_rank_or_clear_a_learner", "ghostwrite_fabricate_publish_present_or_release_without_authorized_human_review"],
    ),
    "career_whole_life_goal": (
        ["rounds-role-duty-life", "rounds-credentials-career-future"], ["resident_private", "whole_life_private"], ["MR-DATA-0", "MR-DATA-2", "MR-DATA-W", "MR-DATA-M", "MR-DATA-R"],
        "rounds/04-N-Navigate-Supervision-Development-and-Career.md",
        ["bank_tax_identity_immigration_medical_or_account_record", "third_party_private_family_relationship_or_health_narrative"],
        ["transact_apply_negotiate_or_send", "make_legal_tax_financial_immigration_match_employment_or_wellbeing_determination"],
    ),
    "agent_definition": (
        [item[0] for item in WORKSPACES], ["resident_private", "synthetic_learning"], ["MR-DATA-0", "MR-DATA-1", "MR-DATA-2", "MR-DATA-M", "MR-DATA-R"],
        "rounds/06-S-Steward-AI-Agents-Data-and-the-Future.md",
        ["patient_event_evaluation_or_restricted_payload_in_prompt_context_or_memory", "undeclared_tool_source_destination_child_agent_or_secret"],
        ["self_activate_self_approve_self_expand_or_extend_expiry", "enable_p3_p4_p5_recursive_delegation_background_service_or_external_executor"],
    ),
    "agent_run_receipt": (
        [item[0] for item in WORKSPACES], ["resident_private", "synthetic_learning"], ["MR-DATA-M", "MR-DATA-R"],
        "rounds/06-S-Steward-AI-Agents-Data-and-the-Future.md",
        ["sensitive_prompt_output_trace_embedding_or_tool_payload", "resolvable_official_identifier_url_token_or_content_fingerprint"],
        ["claim_action_release_acknowledgment_or_completion", "hide_retry_failure_transfer_permission_drift_or_unpurged_state"],
    ),
    "human_approval_receipt": (
        [item[0] for item in WORKSPACES], ["resident_private", "synthetic_learning"], ["MR-DATA-M", "MR-DATA-R"],
        "core/02-ROUNDS-ATTEND-CIRCLE-ORBIT-Operating-Core.md",
        ["signature_credential_contact_secret_or_sensitive_artifact_body", "copied_institutional_approval_attestation_or_authorization_record"],
        ["impersonate_an_attending_program_institution_reviewer_or_release_owner", "carry_approval_across_changed_content_context_source_model_tool_destination_or_expiry"],
    ),
}
RECORD_BASE_PROHIBITED_CONTENT = [
    "patient_phi_real_case_or_reconstructable_clinical_narrative",
    "formal_evaluation_milestone_ccc_peer_review_event_personnel_or_learner_content",
    "restricted_institutional_research_participant_or_employer_content",
    "credential_password_token_key_signature_recovery_code_or_other_secret",
    "unclassified_or_cross_partition_payload",
]
RECORD_BASE_PROHIBITED_ACTIONS = [
    "live_care_diagnosis_treatment_triage_prescribing_dosing_ordering_charting_or_monitoring",
    "external_send_page_submit_publish_release_or_official_system_write",
    "authority_supervision_competence_credential_fitness_or_approval_determination",
    "cross_lane_cross_partition_lookup_merge_or_transfer",
    "ranking_scoring_prediction_surveillance_coercion_or_hidden_reporting",
    "background_execution_hidden_retry_recursive_delegation_or_permission_expansion",
]
DATA_CLASS_IDS = [
    "MR-DATA-0", "MR-DATA-1", "MR-DATA-2", "MR-DATA-W", "MR-DATA-M", "MR-DATA-P",
    "MR-DATA-A", "MR-DATA-R", "MR-DATA-C", "MR-DATA-E", "MR-DATA-S", "MR-DATA-X",
]
ADMITTED_DATA_CLASSES = DATA_CLASS_IDS[:8]
PERSONAL_ADMITTED_DATA_CLASSES = ["MR-DATA-0", "MR-DATA-1", "MR-DATA-2", "MR-DATA-W", "MR-DATA-M", "MR-DATA-R"]
INSTITUTIONAL_DECLARED_UNAVAILABLE = ["MR-DATA-P", "MR-DATA-A"]
PROHIBITED_DATA_CLASSES = DATA_CLASS_IDS[8:]
PROFILE_PROVENANCE_FIELDS = [
    "product_id", "lane", "foundation_namespace", "namespace", "canonical_route",
    "display_name", "resident_status", "local_title", "program", "specialty", "pgy", "site", "rotation_or_service",
    "role_adapters", "primary_role_adapter", "task_hats", "primary_task_hat", "secondary_task_hat",
    "mission_statement", "core_values", "current_priorities", "goals", "record_scopes", "active_record_scope_id",
    "active_partition", "declared_contexts", "active_deployment_context", "institutional_context_available",
    "supervision_context", "supervision_state", "practice_boundaries", "data_boundary", "ai_preferences",
    "memory_preferences", "governance_preferences", "whole_life_available", "recommended_assets",
]
SYSTEM_PROFILE_FIELDS = {
    "product_id", "lane", "foundation_namespace", "namespace", "canonical_route", "record_scopes", "declared_contexts",
    "active_deployment_context", "institutional_context_available", "supervision_context", "supervision_state", "practice_boundaries",
    "data_boundary", "ai_preferences", "memory_preferences", "governance_preferences", "whole_life_available", "recommended_assets",
}

EXPECTED_MATRIX_COLUMNS = (
    "control_id", "screen", "control", "intended_behavior", "implementation_target", "persisted_data",
    "required_permission", "offline_behavior", "error_behavior", "verification_test", "status",
)
EXPECTED_CONTROL_LEDGER_COLUMNS = ("Test ID", "Area", "Priority", "Verification target", "Required evidence", "Result")
EXPECTED_INTEGRATION_LEDGER_COLUMNS = ("Test ID", "Scenario", "Priority", "Expected result", "Required evidence", "Result")
EXPECTED_CANONICAL_LEDGER_COLUMNS = (
    "Canonical ID", "Priority", "Source requirement", "Target disposition", "Required proof", "Evidence path",
    "Source / version", "Owner", "Timestamp", "Remediation", "Result",
)

EXPECTED_MATRIX_ROWS = 216
EXPECTED_INTEGRATION_ROWS = 48
EXPECTED_CANONICAL_ROWS = 160
EXPECTED_TOTAL_EXECUTION_RECORDS = 424

CONTROL_GROUP_CONTRACTS = {
    "APP": ("authenticated loopback application shell", "authenticated resident owner; no agent permission", "minimum configuration and content-free session/security receipt", "invalid Host/Origin/CSRF/session, second-instance, restart and offline fixture", "request denied or prior valid state preserved; no unapproved listener, route or outbound call"),
    "AUTH": ("server-owned identity, ATTEND and authority service", "authenticated resident owner; consequential state remains unverified until authorized-human confirmation", "resident-reported context, source/version/owner/expiry and content-free decision receipt", "missing, stale, expired, conflicting, free-text-approval and title/PGY inflation fixture", "Unverified — authorized human confirmation required; no authority, approval or promotion transition"),
    "DATA": ("pre-echo data-admission gateway", "local P0 classification only; no provider, agent or tool before admission", "classification outcome and content-free trace only; rejected payload has zero residue", "prohibited and evasive canary for the named control across UI, API, file, log, index, memory, backup and provider mocks", "rejected before echo/transformation/persistence; zero model, agent, tool and external-action calls"),
    "CTX": ("server-owned lane, scope, partition and context router", "authenticated owner inside one private ROUNDS context", "exact owner/lane/scope/partition/hat keys plus content-free invalidation receipt", "cross-lane, cross-scope, cross-partition, stale-cache, free-text activation and incompatible-import fixture", "cross-boundary request denied; affected cache and approvals invalidated; no institutional route or store"),
    "GOV": ("server-owned EDENA, stop and lifecycle policy engine", "P0 policy evaluation; human review cannot enable an absent executor", "tier, independent stop, artifact hash, policy version and content-free transition receipt", "forbidden lifecycle skip, nonwaivable stop override, MRREF completion attempt and changed-artifact replay", "unsafe transition denied; state remains at or before Approved Plan and external-action state remains Off"),
    "MISSION": ("transactional mission and five-stage loop service", "authenticated owner; P0 local workflow", "admitted mission state, versions, measures, stage history and tombstone", "invalid stage skip, concurrent edit, downstream-stale and delete/reopen fixture", "atomic valid transition or rollback to prior version with downstream approvals invalidated"),
    "ART": ("versioned local artifact service", "authenticated owner; export and external use remain human-controlled draft operations", "admitted artifact versions, source map, hashes, review state and tombstone", "changed-content approval replay, invented evidence, rights failure, MRREF completion and deletion/restart fixture", "draft/version transition is atomic; unsafe promotion blocked and approval invalidated"),
    "SRC": ("source, claim and citation registry", "P0 public-source read or exact approved P2 one-run read", "source identity/version/date/applicability/claim map/reviewer/expiry; no retrieved instruction authority", "missing, stale, conflicting, fabricated, rights-restricted and prompt-injected source fixture", "source remains unresolved/blocked with visible limits; no invented citation or policy/authority upgrade"),
    "MEM": ("category-consent local memory service", "authenticated owner; memory Off/session-only by default", "only owner-approved admitted category with purpose, scope, provenance, expiry and deletion tombstone", "unconsented, prohibited, raw-Soul, cross-scope, expired, forget/delete/restart and backup fixture", "no recall or persistence outside consent; forget/delete survives restart and backup excludes removed content"),
    "PWR": ("ROUNDS power catalog and state machine", "P0 preview only until exact bounded approval; no permission inheritance", "power ID, source identity, preview hash and inactive/bounded state receipt", "direct activation, multi-power activation, expired approval, forbidden data/action and reinstall fixture", "power remains Available Inactive or returns there; no agent, tool, permission or action is enabled"),
    "WF": ("guided workflow router", "P0 local preview/preparation only", "workflow ID, safe scope, admitted draft state and content-free stop receipt", "real-case, institutional, cross-scope, unsafe-stage and external-action fixture", "workflow blocks or returns a clean fictional/public preparation path without unsafe persistence or action"),
    "AGENT": ("ORBIT agent registry, permission broker and kill service", "PERM-P0 Disabled by default; only exact per-agent P1/P2 one-run contract where available", "charter/hash, bounded permission, invocation count, terminal state and content-free receipt", "permission/mode/data/output/router escalation, AGT-05/06 P1/P2, P3/P4/P5, recursion, retry, timeout and child-agent fixture", "request denied or one bounded run returns to P0; zero hidden retry, delegation, destination or residual temporary state"),
    "AI": ("provider-neutral authenticated backend adapter", "server-side provider access only after owner consent and data admission", "secret-free provider health/capability/model/session/stream/cancel terminal receipt", "missing provider, bad secret, forged capability, canned response, stream reorder, cancel, timeout and tool-event fixture", "truthful unavailable/failed/canceled/completed state; cancellation stops server work and no fabricated event appears"),
    "CAP": ("internal nonclinical capability evidence ledger", "authenticated owner plus named scope-matched human process review", "eligible evidence hash, independent domain mapping, contributions, review, expiry and tombstone", "starter/system/private-life/formal-evaluation/reused-artifact/failed-critical-control evidence fixture", "ineligible or reused evidence earns zero progress; no badge changes permission or asserts competence/credential"),
    "A11Y": ("accessible local user interface and degraded Markdown path", "authenticated owner; no AI permission required", "only user accessibility preferences and content-free conformance receipt", "keyboard-only, screen-reader, focus, contrast, zoom/reflow, reduced-motion and error-language fixture", "same task remains operable or a visible blocker is recorded; no hidden/no-op control"),
    "REC": ("pause, reset, backup, restore, update, rollback and uninstall service", "authenticated owner plus exact destructive-action confirmation", "versioned manifest, migration/checkpoint/tombstone inventory and content-free recovery receipt", "interruption, corrupt/tampered backup, wrong owner/path/version, low disk, rollback and unrelated-sentinel fixture", "operation aborts or rolls back atomically; unrelated data and the last valid state remain unchanged"),
    "PKG": ("reproducible package, migration, launcher and diagnostic layer", "local installer after approved Activation Card", "manifest/checksums/lockfile/licenses/schema/seed versions and install receipt", "tampered archive, unsafe path, missing dependency/license, duplicate migration, unsupported OS and dirty-target fixture", "installation refuses or safely resumes with exact blocker; no partial service, database or launcher claim"),
}
CRITICAL_CONTROL_GROUPS = {"APP", "AUTH", "DATA", "CTX", "GOV", "MEM", "PWR", "AGENT", "AI", "REC"}
CANONICAL_INSTITUTION_ONLY_IDS = {"C5", "D6", "F3", "G7", "K2", "K6", "L1", "INT06", "INT09"}
CANONICAL_MIXED_IDS = {
    "A1", "A2", "A3", "A5", "A7", "A8", "B4", "B7", "C7", "D5", "D8",
    "E1", "E4", "E7", "E8", "F2", "F5", "F6", "G1", "G3", "G4", "G5", "H8",
    "I3", "I7", "J1", "J8", "K4", "K8", "L4", "L6", "L8", "M6", "N1", "N3", "N7",
    "N8", "O3", "P7", "P8", "Q6", "Q7", "R1", "R2", "R7", "INT01", "INT05",
    "INT10", "INT13", "INT15",
}
CANONICAL_NEGATIVE_IDS = {
    "A6", "B2", "B6", "B8", "C1", "C2", "C3", "C4", "C6", "C8",
    "D1", "D2", "D3", "D7", "E3", "E5", "E6", "F8", "G2", "G6",
    "G8", "H3", "H5", "H6", "H7", "I1", "I2", "I4", "I6", "J2",
    "J3", "J7", "K1", "K3", "K5", "K7", "L2", "L7", "M3", "M4",
    "M8", "N6", "O4", "O5", "O7", "P1", "P2", "P3", "P4",
    "P5", "P6", "Q4", "Q5", "Q8", "INT08", "INT12",
}
CANONICAL_SPECIAL_PROOFS = {
    "E8": "Exercise Minimum Mode with a fictional/personal capacity fixture: prove relief questions, manual escalation and protected-life planning, while the app never claims an actual duty handoff was accepted, completed or reconciled; owner text and MRREF cannot close it.",
    "F5": "Use only an unmistakably fictional/process-only dependency. Prove it remains open until fictional human-review evidence; reject real sender, receiver, attending, patient, acknowledgment or responsibility content, and prove owner text/MRREF cannot close the loop.",
    "G1": "Exercise the named sender/receiver/owner/contingency/expiry structure only in an unmistakably fictional rehearsal. Reject real handoff content and prove no owner text, locally generated MRREF or typed acknowledgment becomes a real acceptance or responsibility transfer.",
    "G3": "Exercise an unmistakably fictional consult rehearsal with question/urgency/attempt/follow-up fields, then reject any real consultant, patient, contact, acknowledgment or destination; prove zero contact and that text/MRREF cannot create acknowledgment.",
    "G4": "Exercise attributed recommendations only in a fictional/process rehearsal and keep all decisions human. Reject any real consultant, primary-team, attending or patient content and prove no inferred authority, acceptance or responsibility transfer.",
    "G5": "Exercise fictional delayed/unacknowledged-loop escalation without false closure. Reject real sender/receiver/attending/acknowledgment content and prove owner text/MRREF cannot close or reconcile the loop.",
    "G7": "Prove the personal target cannot create, import, reconcile or verify a real transition output and has no official-system destination. An optional owner note remains resident-reported_external_status_unverified, expires, and cannot advance Authorized Execution, Completed Action or Evaluated Outcome.",
    "L6": "Exercise attribution with public or unmistakably synthetic contributors only; reject identifiable learner, patient, team or community stories and prove zero sensitive persistence, model/agent/tool use, badge evidence or export.",
    "Q6": "Show a human owner role and generic external destination category for planning only. Reject official identifiers, URLs, receipts, signatures and attestations; prove the reference cannot release, reconcile or advance any lifecycle state.",
    "INT05": "Exercise ATTEND against eligible personal/public/synthetic artifacts across relevant hats and scopes; prove the graduated-responsibility fields remain unverified/resident-reported and prove complete absence/rejection of every real clinical artifact path.",
}
CANONICAL_SOURCE_PATH = "source/rounds-domain-pack/tests/ROUNDS-Release-Assurance.md"
CANONICAL_SOURCE_REFERENCE = f"`{CANONICAL_SOURCE_PATH}` / `{ROUNDS_TREE_HASHES['tests/ROUNDS-Release-Assurance.md']}`"
CANONICAL_OWNER = "Unassigned — Hermes must record accountable human/test owner"
ARTIFACT_LIFECYCLE_REACHABLE = ["Exploration", "Simulation", "Recommendation", "Draft Artifact", "Approved Plan"]
ARTIFACT_LIFECYCLE_UNREACHABLE = ["Authorized Execution", "Completed Action", "Evaluated Outcome"]
ORBIT_LIFECYCLE = ["Disabled", "Requested", "Classified", "Scoped", "Previewed", "Synthetic-Tested", "Human-Authorized", "Running-One-Bounded-Run", "Awaiting-Human-Review", "Accepted-or-Rejected", "Human-Released-if-applicable", "Archived-or-Expired-or-Revoked"]
ORBIT_PERSONAL_REACHABLE = ["Disabled", "Requested", "Classified", "Scoped", "Previewed", "Synthetic-Tested", "Human-Authorized", "Running-One-Bounded-Run", "Awaiting-Human-Review", "Accepted-or-Rejected", "Archived-or-Expired-or-Revoked"]
ORBIT_PERSONAL_UNREACHABLE = ["Human-Released-if-applicable"]
ORBIT_PERSONAL_FORWARD = "Disabled -> Requested -> Classified -> Scoped -> Previewed -> Synthetic-Tested -> Human-Authorized -> Running-One-Bounded-Run -> Awaiting-Human-Review -> Accepted-or-Rejected -> Archived-or-Expired-or-Revoked"
ORBIT_PERSONAL_EARLY_TERMINATION = "Any nonterminal state may terminate only to Archived-or-Expired-or-Revoked and return permission to P0; no release state is entered."
LIVE_BACKEND_ONLY_RECORD_IDS = ["CTL-AI-002", "CTL-AI-003", "CTL-AI-004", "CTL-AI-005", "CTL-AI-006", "CTL-AI-007", "INT-044"]
MRREF_CONTRACT = {
    "data_class": "MR-DATA-R",
    "pattern": "^MRREF-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    "resolvable_by_app": False,
    "stores_external_identifier_or_mapping": False,
    "is_official_reference": False,
    "can_advance_artifact_lifecycle": False,
    "owner_note_label_if_used": "resident-reported_external_status_unverified",
    "reject": [
        "direct_identifier", "patient_case_event_evaluation_or_personnel_identifier", "url_or_uri",
        "token_secret_or_credential", "encoded_or_mapped_restricted_payload",
    ],
}

# Filled after the staged contracts are frozen. A mismatch means semantic drift.
CONTROL_ID_DIGEST = "22995145abcfb0cdc7b68ca0bec678a3c03b84bda0103a4f2f82da9a630f008e"
MATRIX_SEMANTIC_DIGEST = "19dc719a91c996a19e043cb89b80addb73671de675ca90bc8e09f412abb2dc43"
INTEGRATION_SEMANTIC_DIGEST = "86603c1548a5a80d4048835f38114b667674816d5731ca494004eb284bb9a58f"
CAPABILITY_DIGEST = "e753a93258ec28883520b019e5f31cb955510d0a3be216ef06f4710e2c38f602"
SOURCE_REGISTRY_DIGEST = "e88a5f2c17b3765f1fa7538a87ac3989456d26df0be553851dc353a77219012b"

STAGING_REQUIRED = (
    ".env.example", "BUILD-STATUS.md", "CHANGELOG.md", "GIVE-THIS-PACKAGE-TO-HERMES.md", "INPUT-PRECEDENCE.md",
    "INSTALL.md", "LICENSE-NOTICE.md", "OPERATOR_HANDOFF.md", "PROCESSING_MESSAGE.md", "README-FIRST.md", "README.md",
    "SOURCE-NOTES.md", "START_HERE.md", "VERSION",
    "config/MR-Agent-Registry.v1.json", "config/MR-Capability-Mastery-Criteria.v1.json", "config/MR-Governance-Policy.v1.json",
    "config/MR-Source-Recommendation-Registry.v1.json", "config/MR-ROUNDS-Catalog.v1.json",
    "config/MR-Professional-Schema-Registry.v1.json",
    "implementation/GAP_ANALYSIS.md", "implementation/HERMES-FINAL-HANDOFF-REPORT-TEMPLATE.md",
    "implementation/HERMES-HANDOFF-README.md", "implementation/MR-Acceptance-and-Test-Ledger.md",
    "implementation/MR-Agent-Team-and-Routing.md", "implementation/MR-Architecture-and-Data-Model.md",
    "implementation/MR-Baseline-Gap-Report.md", "implementation/MR-Capability-and-Badge-Evidence-Model.md",
    "implementation/MR-Control-Completeness-Matrix.csv", "implementation/MR-Governance-EDENA-and-Data-Boundaries.md",
    "implementation/MR-Guide-Page-Content.md", "implementation/MR-Personalization-Mapping-Crosswalk.md",
    "implementation/MR-Product-Specification.md", "implementation/MR-Security-and-Privacy-Checklist.md",
    "implementation/MR-Starter-Workspace-Crosswalk.md", "implementation/MR-Synthetic-Sample-Mission.md",
    "implementation/MR-Technical-Implementation-Guide.md", "implementation/MR-User-Installation-Guide.md",
    "personalization/ROUNDS-Discover-Packet.synthetic.example.json", "personalization/ROUNDS-Mission-Profile.synthetic.example.json",
    "personalization/ROUNDS-Soul-Profile.synthetic.example.json", "personalization/README.md",
    "schemas/ROUNDS-Discover-Packet.schema.json", "schemas/ROUNDS-Mission-Profile.schema.json", "schemas/ROUNDS-Soul-Profile.schema.json",
)

RELEASE_REQUIRED = STAGING_REQUIRED + (
    "RELEASE-MANIFEST.json", "SHA256SUMS.txt", "SOURCE-INVENTORY.json", "implementation/MR-Functional-Build-Master-Prompt.md",
    "personalization/input-schemas/discover-packet-input.schema.json", "personalization/input-schemas/soul-profile-input.schema.json",
    "source/original-functional-build-master-prompt.md", "source/archives/DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0.zip",
    "source/archives/Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Package-v1.0.zip",
    "source/complete-reference/Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Hermes-Program.md",
    "source/complete-reference/Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Setup-Guide.md",
    "source/complete-reference/Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Setup-Guide.docx",
    "source/baseline-application/RELEASE-MANIFEST.json", "source/baseline-application/SHA256SUMS.txt", "tools/verify-build-kit.py",
    *(f"source/rounds-domain-pack/{name}" for name in ROUNDS_TREE_HASHES),
    *(f"source/legacy-reference/{name}" for name in COMPLETE_TREE_HASHES),
)

PLACEHOLDERS = (
    "[PACKAGE_NAME]", "[SOURCE_DIRECTORY_OR_REPOSITORY]", "[DISCOVER_PACKET_PATH_OR_SOURCE]",
    "[SOUL_QUIZ_RESULTS_PATH_OR_SOURCE]", "[HERMES_PROFILE_NAME_OR_AUTO_DETECT]", "[USER_TYPE]", "[ROLE_LANES]",
    "[DOMAIN]", "[AGENT_LIST]", "[DATA_CLASSIFICATION]", "[DOMAIN_GUARDRAILS]", "[MACOS_WINDOWS_LINUX]",
    "[ZIP_INSTALLER_DESKTOP_APP_LOCAL_WEB_APP]",
)


class Checks:
    def __init__(self) -> None:
        self.passed: list[str] = []
        self.failed: list[str] = []
        self.warnings: list[str] = []

    def check(self, condition: bool, label: str, detail: Any = None) -> bool:
        if condition:
            self.passed.append(label)
            print(f"PASS  {label}")
            return True
        suffix = "" if detail in (None, "", [], {}) else f" — {detail}"
        self.failed.append(label + suffix)
        print(f"FAIL  {label}{suffix}")
        return False

    def warn(self, label: str, detail: Any = None) -> None:
        suffix = "" if detail in (None, "", [], {}) else f" — {detail}"
        self.warnings.append(label + suffix)
        print(f"WARN  {label}{suffix}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256((payload + "\n").encode()).hexdigest()


def canonical_record_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def strict_json_loads(text: str) -> Any:
    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key!r}")
            result[key] = value
        return result
    def reject_constant(value: str) -> Any:
        raise ValueError(f"non-finite JSON number: {value}")
    return json.loads(text, object_pairs_hook=pairs_hook, parse_constant=reject_constant)


def files(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        return {}
    return {path.relative_to(root).as_posix(): path for path in sorted(root.rglob("*")) if path.is_file() and not path.is_symlink()}


def tree_hashes(root: Path) -> dict[str, str]:
    return {name: sha256(path) for name, path in files(root).items()}


def tree_digest(values: dict[str, str]) -> str:
    payload = "".join(f"{digest}  {name}\n" for name, digest in sorted(values.items()))
    return hashlib.sha256(payload.encode()).hexdigest()


def load_json(c: Checks, path: Path, label: str) -> Any | None:
    try:
        value = strict_json_loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        c.check(False, label, error)
        return None
    c.check(True, label)
    return value


def strict_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return type(left) is type(right) and left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(strict_equal(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(strict_equal(a, b) for a, b in zip(left, right))
    return left == right


def json_type_matches(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict), "array": isinstance(value, list), "string": isinstance(value, str),
        "boolean": isinstance(value, bool), "null": value is None,
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
    }.get(expected, False)


def resolve_ref(root: dict[str, Any], reference: str) -> Any:
    if not reference.startswith("#/"):
        raise ValueError(f"unsupported external or malformed $ref: {reference}")
    value: Any = root
    for raw in reference[2:].split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, dict) or key not in value:
            raise ValueError(f"unresolved $ref: {reference}")
        value = value[key]
    return value


SCHEMA_KEYWORDS = {
    "$schema", "$id", "$ref", "$defs", "title", "description", "type", "const", "enum", "not", "allOf", "anyOf", "oneOf",
    "if", "then", "else", "properties", "patternProperties", "additionalProperties", "required", "minProperties", "maxProperties",
    "items", "prefixItems", "contains", "minContains", "maxContains", "minItems", "maxItems", "uniqueItems",
    "minLength", "maxLength", "pattern", "format", "minimum", "maximum",
    # Normative runtime rule annotation. The in-package validator asserts its
    # exact content; JSON Schema alone cannot compare two date-time values.
    "x-runtime-temporal-constraints",
}


def unsupported_schema_keywords(schema: Any) -> list[str]:
    errors: list[str] = []
    def visit(node: Any, path: str) -> None:
        if isinstance(node, bool):
            return
        if not isinstance(node, dict):
            errors.append(f"{path}: schema node is not an object or boolean")
            return
        for key in node:
            if key not in SCHEMA_KEYWORDS:
                errors.append(f"{path}: unsupported keyword {key!r}")
        for key in ("not", "if", "then", "else", "items", "contains", "additionalProperties"):
            value = node.get(key)
            if isinstance(value, (dict, bool)):
                visit(value, f"{path}.{key}")
        for key in ("allOf", "anyOf", "oneOf", "prefixItems"):
            for index, value in enumerate(node.get(key, [])):
                visit(value, f"{path}.{key}[{index}]")
        for key in ("properties", "patternProperties", "$defs"):
            for name, value in node.get(key, {}).items():
                visit(value, f"{path}.{key}.{name}")
    visit(schema, "$")
    return errors


def validate_json_schema(instance: Any, schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    def walk(value: Any, rule: Any, path: str, depth: int = 0) -> None:
        if depth > 100:
            errors.append(f"{path}: schema recursion limit")
            return
        if isinstance(rule, bool):
            if not rule:
                errors.append(f"{path}: disallowed by schema")
            return
        if not isinstance(rule, dict):
            errors.append(f"{path}: malformed schema node")
            return
        if "$ref" in rule:
            try:
                target = resolve_ref(schema, rule["$ref"])
            except Exception as error:
                errors.append(f"{path}: {error}")
                return
            walk(value, target, path, depth + 1)
            siblings = {key: item for key, item in rule.items() if key != "$ref"}
            if siblings:
                walk(value, siblings, path, depth + 1)
            return
        if "const" in rule and not strict_equal(value, rule["const"]):
            errors.append(f"{path}: const mismatch")
        if "enum" in rule and not any(strict_equal(value, item) for item in rule["enum"]):
            errors.append(f"{path}: outside enum")
        if "not" in rule:
            before = len(errors)
            walk(value, rule["not"], path, depth + 1)
            matched = len(errors) == before
            del errors[before:]
            if matched:
                errors.append(f"{path}: matched forbidden schema")
        expected_type = rule.get("type")
        if expected_type is not None:
            choices = expected_type if isinstance(expected_type, list) else [expected_type]
            if not any(json_type_matches(value, item) for item in choices):
                errors.append(f"{path}: expected type {expected_type!r}")
                return
        for branch in rule.get("allOf", []):
            walk(value, branch, path, depth + 1)
        if "anyOf" in rule:
            matches = 0
            for branch in rule["anyOf"]:
                before = len(errors)
                walk(value, branch, path, depth + 1)
                if len(errors) == before:
                    matches += 1
                else:
                    del errors[before:]
            if not matches:
                errors.append(f"{path}: no anyOf branch")
        if "oneOf" in rule:
            matches = 0
            for branch in rule["oneOf"]:
                before = len(errors)
                walk(value, branch, path, depth + 1)
                if len(errors) == before:
                    matches += 1
                else:
                    del errors[before:]
            if matches != 1:
                errors.append(f"{path}: expected one oneOf match, observed {matches}")
        if "if" in rule:
            before = len(errors)
            walk(value, rule["if"], path, depth + 1)
            condition = len(errors) == before
            del errors[before:]
            branch = rule.get("then") if condition else rule.get("else")
            if branch is not None:
                walk(value, branch, path, depth + 1)
        if isinstance(value, dict):
            for key in rule.get("required", []):
                if key not in value:
                    errors.append(f"{path}: missing {key!r}")
            properties = rule.get("properties", {})
            patterns = rule.get("patternProperties", {})
            for key, item in value.items():
                matched = False
                if key in properties:
                    walk(item, properties[key], f"{path}.{key}", depth + 1)
                    matched = True
                for pattern, branch in patterns.items():
                    if re.search(pattern, key):
                        walk(item, branch, f"{path}.{key}", depth + 1)
                        matched = True
                if not matched:
                    additional = rule.get("additionalProperties", True)
                    if additional is False:
                        errors.append(f"{path}: unknown property {key!r}")
                    elif isinstance(additional, (dict, bool)):
                        walk(item, additional, f"{path}.{key}", depth + 1)
            if "minProperties" in rule and len(value) < rule["minProperties"]:
                errors.append(f"{path}: too few properties")
            if "maxProperties" in rule and len(value) > rule["maxProperties"]:
                errors.append(f"{path}: too many properties")
        if isinstance(value, list):
            if "minItems" in rule and len(value) < rule["minItems"]:
                errors.append(f"{path}: too few items")
            if "maxItems" in rule and len(value) > rule["maxItems"]:
                errors.append(f"{path}: too many items")
            if rule.get("uniqueItems"):
                frozen = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value]
                if len(frozen) != len(set(frozen)):
                    errors.append(f"{path}: duplicate items")
            prefixes = rule.get("prefixItems", [])
            for index, prefix in enumerate(prefixes[:len(value)]):
                walk(value[index], prefix, f"{path}[{index}]", depth + 1)
            item_rule = rule.get("items")
            if isinstance(item_rule, (dict, bool)):
                for index in range(len(prefixes), len(value)):
                    walk(value[index], item_rule, f"{path}[{index}]", depth + 1)
            if "contains" in rule:
                matched = 0
                for item in value:
                    before = len(errors)
                    walk(item, rule["contains"], path, depth + 1)
                    if len(errors) == before:
                        matched += 1
                    else:
                        del errors[before:]
                if matched < rule.get("minContains", 1) or ("maxContains" in rule and matched > rule["maxContains"]):
                    errors.append(f"{path}: contains matched {matched}")
        if isinstance(value, str):
            if "minLength" in rule and len(value) < rule["minLength"]:
                errors.append(f"{path}: too short")
            if "maxLength" in rule and len(value) > rule["maxLength"]:
                errors.append(f"{path}: too long")
            if "pattern" in rule and not re.search(rule["pattern"], value):
                errors.append(f"{path}: pattern mismatch")
            if rule.get("format") == "uuid":
                try:
                    parsed = uuid.UUID(value)
                except (ValueError, AttributeError):
                    errors.append(f"{path}: invalid UUID")
                else:
                    if str(parsed) != value.casefold():
                        errors.append(f"{path}: noncanonical UUID")
            if rule.get("format") == "date-time":
                candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
                try:
                    parsed = datetime.fromisoformat(candidate)
                except ValueError:
                    errors.append(f"{path}: invalid date-time")
                else:
                    if parsed.tzinfo is None:
                        errors.append(f"{path}: date-time lacks offset")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in rule and value < rule["minimum"]:
                errors.append(f"{path}: below minimum")
            if "maximum" in rule and value > rule["maximum"]:
                errors.append(f"{path}: above maximum")
    walk(instance, schema, "$")
    return errors


def safe_name(name: str) -> bool:
    if not name or "\x00" in name or "\\" in name or name.startswith("/") or "//" in name:
        return False
    candidate = name[:-1] if name.endswith("/") else name
    if not candidate:
        return False
    parts = candidate.split("/")
    pure = PurePosixPath(candidate)
    return all(part not in {"", ".", ".."} and ":" not in part for part in parts) and not pure.is_absolute() and pure.parts == tuple(parts)


def parse_checksums(path: Path) -> tuple[dict[str, str], list[str]]:
    values: dict[str, str] = {}
    errors: list[str] = []
    folded: set[str] = set()
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        digest, separator, relative = line.partition("  ")
        key = unicodedata.normalize("NFC", relative).casefold()
        if separator != "  " or not re.fullmatch(r"[0-9a-f]{64}", digest) or not safe_name(relative) or relative.endswith("/") or relative in values or key in folded:
            errors.append(f"line {number}")
            continue
        values[relative] = digest
        folded.add(key)
    return values, errors


def markdown_table_rows(text: str) -> list[list[str]]:
    result: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            cells: list[str] = []
            current: list[str] = []
            index = 1
            while index < len(stripped) - 1:
                character = stripped[index]
                if character == "\\" and index + 1 < len(stripped) - 1 and stripped[index + 1] == "|":
                    current.append("|")
                    index += 2
                    continue
                if character == "|":
                    cells.append("".join(current).strip())
                    current = []
                else:
                    current.append(character)
                index += 1
            cells.append("".join(current).strip())
            result.append(cells)
    return result


def expected_canonical_ids() -> list[str]:
    values = [f"{letter}{index}" for letter in "ABCDEFGHIJKLMNOPQR" for index in range(1, 9)]
    values.extend(f"INT{index:02d}" for index in range(1, 17))
    return values


def canonical_source_rows(path: Path) -> list[tuple[str, str, str]]:
    if not path.is_file() or sha256(path) != ROUNDS_TREE_HASHES["tests/ROUNDS-Release-Assurance.md"]:
        return []
    pattern = re.compile(
        r"^- \[ \] \*\*(?P<id>[A-R][1-8]|INT[0-9]{2})(?: (?P<critical_inside>CRITICAL))?\*\*"
        r"(?: \*\*(?P<critical_after>CRITICAL)\*\*)? — (?P<requirement>.+)$"
    )
    rows: list[tuple[str, str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if match:
            priority = "Critical" if match.group("critical_inside") or match.group("critical_after") else "Required"
            rows.append((match.group("id"), priority, match.group("requirement")))
    return rows


def canonical_target_disposition(test_id: str, requirement: str) -> tuple[str, str]:
    if test_id in CANONICAL_INSTITUTION_ONLY_IDS:
        return (
            "institutional_feature_absence_test",
            CANONICAL_SPECIAL_PROOFS.get(test_id, "Execute the personal-target absence test: prove zero institutional/clinical route, store, bind, connector, executor, permission transition, imported attestation or payload; exercise rejection and the accountable-human external route. Record Passed only with evidence, owner, timestamp and scope rationale; Not applicable is not permitted."),
        )
    if test_id in CANONICAL_MIXED_IDS:
        return (
            "execute_mixed_positive_and_boundary",
            CANONICAL_SPECIAL_PROOFS.get(test_id, "Exercise the intended applicable path and its invalid, prohibited or failure counterpart. Prove the positive observable result plus denial/absence, zero unsafe persistence/model/tool/action, visible safe state, accountable-human route, content-free receipt and restart/replay behavior where applicable."),
        )
    if test_id in CANONICAL_NEGATIVE_IDS:
        return (
            "execute_negative",
            "Exercise the prohibited, invalid or failure path and prove denial/absence, zero unsafe persistence/model/tool/action, visible safe state and human route, and a content-free receipt.",
        )
    return (
        "execute_positive",
        "Exercise the applicable private, public-source or unmistakably fictional path end to end and prove correct state, persistence/restart where relevant, source and authority boundaries, human ownership and inspectable evidence.",
    )


def check_required(c: Checks, package: Path, preassembly: bool) -> None:
    required = STAGING_REQUIRED if preassembly else RELEASE_REQUIRED
    missing = [item for item in required if not (package / item).is_file()]
    empty = [item for item in required if (package / item).is_file() and (package / item).stat().st_size == 0]
    c.check(not missing, "All required contracts and sources exist", missing)
    c.check(not empty, "All required contracts and sources are nonempty", empty)
    c.check((package / "VERSION").read_text(encoding="utf-8").strip() == "1.0.0", "Build-kit VERSION is 1.0.0")


def check_controlled_text(c: Checks, package: Path, preassembly: bool) -> None:
    unresolved: list[str] = []
    residue: list[str] = []
    stale = (
        "BREATHE", "Respiratory-Care", "Respiratory Care", "respiratory-care", "resp_rounds.*",
        "/respiratory-care", "RT-DATA-", "Synthetic ABG", "Ventilator Learning", "NBRC",
        "nurse_practitioner", "/nurse-practitioners/dashboard", "np_wings.*", "np_lppef.*",
        "NP-AGT-", "WINGS-PWR-", "My NP Life, Practice & Purpose Command Center",
        "STAMR_HERE", "REPOMR-TEMPLATE",
    )
    # Only generated/controlled package material is scanned. Immutable source bytes
    # are deliberately excluded: provenance is validated by hash and archive parity.
    for relative, path in files(package).items():
        if relative.startswith("source/"):
            continue
        if path.suffix.lower() not in {".md", ".json", ".csv", ".example", ".txt"} and path.name != "VERSION":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for placeholder in PLACEHOLDERS:
            if placeholder in text:
                unresolved.append(f"{relative}:{placeholder}")
        for token in stale:
            if token in text:
                residue.append(f"{relative}:{token}")
    c.check(not unresolved, "Controlled contracts contain no unresolved functional placeholders", unresolved[:10])
    c.check(not residue, "Generated contracts contain no cross-product or malformed identity residue", residue[:20])


def check_all_json(c: Checks, package: Path) -> None:
    invalid: list[str] = []
    for path in sorted(package.rglob("*.json")):
        try:
            strict_json_loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            invalid.append(f"{path.relative_to(package)}: {error}")
    c.check(not invalid, "Every JSON file strictly parses without duplicate keys or non-finite numbers", invalid[:10])


def check_catalogs(c: Checks, package: Path) -> tuple[Any, Any, Any, Any, Any]:
    catalog = load_json(c, package / "config/MR-ROUNDS-Catalog.v1.json", "ROUNDS catalog parses")
    agents = load_json(c, package / "config/MR-Agent-Registry.v1.json", "Agent registry parses")
    capabilities = load_json(c, package / "config/MR-Capability-Mastery-Criteria.v1.json", "Capability criteria parse")
    sources = load_json(c, package / "config/MR-Source-Recommendation-Registry.v1.json", "Source recommendation registry parses")
    governance = load_json(c, package / "config/MR-Governance-Policy.v1.json", "Governance policy parses")
    professional = load_json(c, package / "config/MR-Professional-Schema-Registry.v1.json", "Professional schema registry parses")
    if isinstance(catalog, dict):
        c.check(catalog.get("schema") == "NAIO-MR-ROUNDS-CATALOG-1" and catalog.get("counts") == {"powers": 24, "workflows": 24, "templates": 30}, "Catalog identity and counts are exact")
        c.check(catalog.get("core_four") == CORE_FOUR and catalog.get("optional_fifth_launcher") is None, "Catalog preserves the exact Core Four and empty fifth launcher")
        c.check([item.get("id") for item in catalog.get("powers", [])] == [f"PWR-{i:02d}" for i in range(1, 25)] and [item.get("display_name") for item in catalog.get("powers", [])] == POWERS, "Exactly twenty-four ordered canonical ROUNDS powers")
        c.check(all(item.get("installation_state") == "available_inactive" and item.get("agent_permission") == "PERM-P0 Disabled" and item.get("external_actions") == "off" for item in catalog.get("powers", [])), "Every ROUNDS power installs inactive, P0 and external-actions off")
        c.check([item.get("id") for item in catalog.get("workflows", [])] == [f"WF-{i:02d}" for i in range(1, 25)] and [item.get("display_name") for item in catalog.get("workflows", [])] == WORKFLOWS, "Exactly twenty-four ordered canonical workflows")
        c.check(all(item.get("installation_state") == "preview_only" and item.get("external_actions") == "off" for item in catalog.get("workflows", [])), "Every workflow installs Preview only")
        c.check([item.get("id") for item in catalog.get("templates", [])] == [f"TPL-{i:02d}" for i in range(1, 31)] and [item.get("display_name") for item in catalog.get("templates", [])] == TEMPLATES, "Exactly thirty ordered canonical templates")
        c.check(catalog.get("power_lifecycle") == ["Available Inactive", "Previewed", "Approved Inactive", "Active Bounded", "Paused", "Removed"], "Power lifecycle is exact")
        c.check(catalog.get("external_action_lifecycle") == ["Off", "Drafted", "Previewed", "Human-Approved-One-Run", "Staged", "Human-Released", "Confirmed-or-Failed", "Closed"], "External-action lifecycle is exact")
        c.check(
            catalog.get("artifact_lifecycle_reachable_in_target") == ARTIFACT_LIFECYCLE_REACHABLE
            and catalog.get("artifact_lifecycle_unreachable_reference_only") == ARTIFACT_LIFECYCLE_UNREACHABLE
            and catalog.get("external_action_lifecycle_reference_only") is True
            and catalog.get("executor_shipped") is False
            and catalog.get("external_action_transitions_available_in_target") == [],
            "Catalog makes execution, completion and outcome states unreachable and ships no executor or transition",
        )
    if isinstance(agents, dict):
        entries = agents.get("entries", [])
        c.check(agents.get("schema") == "NAIO-MR-ROUNDS-AGENT-REGISTRY-1" and [(item.get("id"), item.get("name"), item.get("source_proposed_maximum")) for item in entries] == AGENTS, "Exactly ten canonical ROUNDS agents and source ceilings")
        c.check(all(item.get("installed_permission") == "PERM-P0 Disabled" for item in entries), "All ten agents install PERM-P0 Disabled")
        observed_agents = {item.get("id"): item for item in entries if isinstance(item, dict)}
        exact_agent_contracts = len(observed_agents) == len(entries) == len(AGENT_PERSONAL_CONTRACTS)
        for agent_id, expected in AGENT_PERSONAL_CONTRACTS.items():
            item = observed_agents.get(agent_id, {})
            exact_agent_contracts &= all(strict_equal(item.get(field), value) for field, value in expected.items())
            maximum = expected["personal_maximum"]
            expected_blocked = {
                "PERM-P0": ["PERM-P1", "PERM-P2", "PERM-P3", "PERM-P4", "PERM-P5"],
                "PERM-P1": ["PERM-P2", "PERM-P3", "PERM-P4", "PERM-P5"],
                "PERM-P2": ["PERM-P3", "PERM-P4", "PERM-P5"],
            }[maximum]
            expected_transitions = [] if not expected["personal_available"] else (
                ["P0-to-one-run-P1-to-P0"] if maximum == "PERM-P1"
                else ["P0-to-one-run-P1-to-P0", "P0-to-one-run-P2-to-P0"]
            )
            exact_agent_contracts &= item.get("personal_blocked_permissions") == expected_blocked
            exact_agent_contracts &= item.get("personal_permission_transitions") == expected_transitions
        c.check(exact_agent_contracts, "Every agent has the exact personal availability, ceiling, modes, data, outputs, router and one-run transitions")
        c.check(
            all(
                observed_agents.get(agent_id, {}).get("personal_available") is False
                and observed_agents.get(agent_id, {}).get("personal_maximum") == "PERM-P0"
                and observed_agents.get(agent_id, {}).get("personal_permission_transitions") == []
                and observed_agents.get(agent_id, {}).get("personal_blocked_permissions") == ["PERM-P1", "PERM-P2", "PERM-P3", "PERM-P4", "PERM-P5"]
                and observed_agents.get(agent_id, {}).get("allowed_modes") == []
                and observed_agents.get(agent_id, {}).get("allowed_data_classes") == []
                and observed_agents.get(agent_id, {}).get("allowed_outputs") == []
                and observed_agents.get(agent_id, {}).get("router") == "unavailable_personal_preview_only"
                for agent_id in ("AGT-05", "AGT-06")
            ),
            "AGT-05 and AGT-06 are locked at P0 and reject every P1/P2/P3/P4/P5 route",
        )
        ladder = agents.get("permission_ladder", {})
        c.check(list(ladder) == ["PERM-P0 Disabled", "PERM-P1 Private Nonsensitive or Synthetic Draft", "PERM-P2 Private Approved Read-Only", "PERM-P3 Institution-Approved Read or Sandbox", "PERM-P4 One-Run Staged Nonclinical Write", "PERM-P5 Prohibited"], "Permission ladder is exact P0 through P5")
        p3 = ladder.get("PERM-P3 Institution-Approved Read or Sandbox", "").casefold()
        p4 = ladder.get("PERM-P4 One-Run Staged Nonclinical Write", "").casefold()
        p5 = ladder.get("PERM-P5 Prohibited", "").casefold()
        c.check(
            agents.get("personal_p4_available") is False
            and all(term in p3 for term in ["unavailable", "separately provisioned", "institutional"])
            and all(term in p4 for term in ["unavailable", "separate", "institution", "clinical care", "communication"])
            and all(term in p5 for term in ["autonomous clinical", "patient communication", "evaluation", "recursive delegation"]),
            "P3/P4 are technically unavailable in the personal target and P5 is prohibited",
        )
        forbidden = " ".join(" ".join(item.get("may_not", [])) for item in entries).casefold()
        c.check(all(term in forbidden for term in ["patient", "live patient care", "diagnose", "treat", "triage", "prescribe", "bill", "send or page", "activate itself", "declare role", "recursively delegate"]), "Agent registry carries patient, clinical-action, authority and recursion prohibitions")
        c.check(agents.get("orbit_framework") == ["Objective & owner", "Role, risk & responsibility", "Boundaries & budget", "Inspect & test", "Transfer or terminate"], "ORBIT framework is exact")
        c.check(
            agents.get("whole_life_private_agent_access") is False
            and all(set(item.get("allowed_data_classes", [])) <= {"MR-DATA-0", "MR-DATA-1", "MR-DATA-2"} for item in entries)
            and all(not set(item.get("allowed_data_classes", [])) & {"MR-DATA-W", "MR-DATA-M", "MR-DATA-R"} for item in entries),
            "Every agent excludes whole-life and control-metadata classes; only exact MR-DATA-0/1/2 subsets may enter payloads",
        )
        c.check(
            agents.get("orbit_lifecycle") == ORBIT_LIFECYCLE
            and agents.get("orbit_personal_reachable_states") == ORBIT_PERSONAL_REACHABLE
            and agents.get("orbit_personal_unreachable_reference_only_states") == ORBIT_PERSONAL_UNREACHABLE
            and agents.get("orbit_personal_forward_transition") == ORBIT_PERSONAL_FORWARD
            and agents.get("orbit_personal_early_termination") == ORBIT_PERSONAL_EARLY_TERMINATION,
            "Agent registry freezes the exact personal ORBIT path and keeps Human-Released reference-only and unreachable",
        )
    if isinstance(capabilities, dict):
        c.check(capabilities.get("schema") == "NAIO-MR-ROUNDS-CAPABILITY-MASTERY-CRITERIA-1" and capabilities.get("status") == "normative_build_layer_contract", "Capability schema identity and status are exact")
        c.check([item.get("name") for item in capabilities.get("levels", [])] == ["Basic", "Intermediate", "Advanced", "AI Agent Orchestration Master"], "Capability mastery chain is exact")
        domains = capabilities.get("domains", [])
        criteria = [criterion for domain in domains for criterion in domain.get("criteria", [])]
        capstone = capabilities.get("global_orchestration_capstone", {}).get("criteria", [])
        c.check(len(domains) == 17 and len(criteria) == 68 and len(capstone) == 9 and capabilities.get("counts") == {"domains": 17, "levels": 4, "domain_criteria": 68, "capstone_criteria": 9, "total_criteria": 77}, "Capability counts are exactly 17/4/68+9=77")
        c.check([item.get("id") for item in domains] == [f"CAP-{i:02d}" for i in range(1, 18)] and all(len(item.get("criteria", [])) == 4 for item in domains), "Capability domains are exact CAP-01..CAP-17 with four criteria each")
        valid_prereqs = True
        for domain in domains:
            ids = [item.get("id") for item in domain.get("criteria", [])]
            valid_prereqs &= ids == [f"{domain.get('id')}-L{i}" for i in range(1, 5)]
            valid_prereqs &= [item.get("prerequisite") for item in domain.get("criteria", [])] == [None, ids[0], ids[1], ids[2]]
        c.check(valid_prereqs, "Capability prerequisites are complete and acyclic")
        expected_levels = [
            ("L1", "Basic", None, "P1", 1, 1, False),
            ("L2", "Intermediate", "L1", "P1", 2, 1, False),
            ("L3", "Advanced", "L2", "P2", 3, 1, False),
            ("L4", "AI Agent Orchestration Master", "L3", "P2", 5, 2, True),
        ]
        level_rows = [
            (
                item.get("id"), item.get("name"), item.get("prerequisite_level"), item.get("agent_permission_ceiling"),
                item.get("minimum_cumulative_distinct_eligible_missions"),
                item.get("minimum_additional_distinct_eligible_missions_since_prior_level"),
                item.get("award_requires_global_capstone"),
            )
            for item in capabilities.get("levels", [])
        ]
        c.check(level_rows == expected_levels, "Capability levels carry exact Basic→Intermediate→Advanced→Orchestration prerequisites, ceilings and mission floors")
        mission_policy = capabilities.get("mission_requirement_policy", {})
        c.check(
            mission_policy.get("monotonic") is True
            and mission_policy.get("by_level") == [
                {"level": level_id, "cumulative": cumulative, "additional_since_prior": additional}
                for level_id, _, _, _, cumulative, additional, _ in expected_levels
            ]
            and all(term in mission_policy.get("semantics", "").casefold() for term in ["cumulative", "additional", "prior-level missions", "cannot be relabeled"]),
            "Capability cumulative and additional mission requirements are exact and monotonic",
        )
        allowed_evidence = {
            "evaluated_mission", "reviewed_artifact", "source_audit", "correction_record", "safety_drill",
            "accessibility_review", "agent_run_receipt", "data_admission_receipt", "permission_envelope",
            "decision_log", "independent_human_review", "provider_capability_receipt",
            "deletion_or_rollback_receipt", "failure_recovery_receipt", "evidence_assignment_record",
        }
        c.check(set(capabilities.get("eligibility", {}).get("allowed_evidence_types", [])) == allowed_evidence, "Capability evidence vocabulary is exact")
        criterion_semantics = True
        descriptions: list[str] = []
        for domain in domains:
            domain_id = domain.get("id")
            policy = domain.get("synthetic_evidence_policy")
            for level_index, criterion in enumerate(domain.get("criteria", []), 1):
                level_id = f"L{level_index}"
                cumulative, additional = expected_levels[level_index - 1][4:6]
                combination = criterion.get("required_evidence_combination", {})
                evidence = criterion.get("eligible_evidence", [])
                description = criterion.get("description")
                descriptions.append(description)
                criterion_semantics &= isinstance(description, str) and len(description) >= 70
                criterion_semantics &= description == criterion.get("observable_rubric")
                criterion_semantics &= criterion.get("minimum_distinct_eligible_missions") == cumulative
                criterion_semantics &= criterion.get("mission_requirement_kind") == "cumulative_floor"
                criterion_semantics &= criterion.get("minimum_cumulative_distinct_eligible_missions") == cumulative
                criterion_semantics &= criterion.get("minimum_additional_distinct_eligible_missions_since_prior_level") == additional
                criterion_semantics &= criterion.get("cumulative_requirement_includes_prior_levels") is True
                criterion_semantics &= criterion.get("requires_human_review") is True
                criterion_semantics &= criterion.get("requires_independent_evidence") is (level_id in {"L3", "L4"})
                criterion_semantics &= criterion.get("agent_permission_ceiling") == expected_levels[level_index - 1][3]
                criterion_semantics &= criterion.get("synthetic_evidence_policy") == policy
                synthetic_requires_public = policy == "process_only_not_sufficient_without_opened_public_sources"
                criterion_semantics &= criterion.get("synthetic_process_evidence_eligible") is str(policy).startswith("process_only")
                criterion_semantics &= criterion.get("synthetic_evidence_requires_opened_public_source_supplement") is synthetic_requires_public
                criterion_semantics &= criterion.get("minimum_opened_public_source_records_when_required") == (1 if synthetic_requires_public else 0)
                criterion_semantics &= isinstance(evidence, list) and len(evidence) >= 2 and len(evidence) == len(set(evidence)) and set(evidence) <= allowed_evidence
                criterion_semantics &= combination == {
                    "all_of": evidence,
                    "distinct_evidence_item_ids": True,
                    "same_artifact_may_not_supply_every_required_item": level_id in {"L3", "L4"},
                }
                criterion_semantics &= criterion.get("evidence_assignment") == {
                    "primary_domain_required": domain_id,
                    "criterion_id_required": f"{domain_id}-{level_id}",
                    "one_evidence_item_id_one_criterion": True,
                    "award_gate": "global_orchestration_capstone" if level_id == "L4" else "domain_criterion",
                }
                if level_id in {"L3", "L4"}:
                    independence = criterion.get("independent_evidence_rule", "").casefold()
                    criterion_semantics &= all(term in independence for term in ["different artifact", "independent", "generating agent"])
                synthetic_limit = criterion.get("synthetic_evidence_limit", "").casefold()
                criterion_semantics &= all(term in synthetic_limit for term in ["fictional", "ai-stewardship", "never", "clinical competence", "institutional authority"])
        c.check(criterion_semantics and len(descriptions) == len(set(descriptions)) == 68 and len({domain.get("focus") for domain in domains}) == 17, "All 68 domain-specific rubrics have exact evidence-set, independence, assignment and synthetic-eligibility semantics")
        c.check(
            {
                domain.get("id")
                for domain in domains
                if all(
                    item.get("synthetic_process_evidence_eligible") is True
                    and item.get("synthetic_evidence_requires_opened_public_source_supplement") is True
                    and item.get("minimum_opened_public_source_records_when_required") == 1
                    for item in domain.get("criteria", [])
                )
            } == {"CAP-03", "CAP-13"},
            "CAP-03 and CAP-13 admit synthetic process evidence only with at least one opened-public-source supplement",
        )
        reuse_policy = capabilities.get("evidence_reuse_policy", {})
        c.check(
            reuse_policy == {
                "one_evidence_item_id_one_criterion": True,
                "one_artifact_hash_maximum_primary_domains": 1,
                "one_artifact_hash_maximum_total_domain_assignments": 2,
                "secondary_domain_assignment_requires_distinct_observable_and_independent_review": True,
                "same_artifact_cannot_satisfy_all_levels_of_one_domain": True,
                "shared_source_citation_is_not_shared_source_audit_evidence": True,
                "capstone_execution_evidence_must_be_new_and_not_consumed_by_domain_prerequisites": True,
                "preloaded_or_system_generated_evidence_reuse": "prohibited",
            },
            "Capability evidence reuse and independence policy is exact",
        )
        capstone_contract = capabilities.get("global_orchestration_capstone", {})
        safety_advanced = [f"{domain.get('id')}-L3" for domain in domains if domain.get("safety_domain") is True]
        capstone_prereqs = capstone_contract.get("prerequisites", {})
        capstone_criteria = capstone_contract.get("criteria", [])
        c.check(
            capstone_contract.get("id") == "CAPSTONE-AI-ORCH-01"
            and capstone_contract.get("required_for_level") == "L4"
            and capstone_contract.get("agent_permission_ceiling") == "P2"
            and capstone_contract.get("external_actions") == "unsupported"
            and capstone_prereqs == {
                "all_advanced_safety_domains_required": True,
                "required_current_domain_criteria": safety_advanced,
                "independent_evidence_required": True,
                "minimum_new_distinct_capstone_missions": 2,
                "minimum_independent_evidence_items": 2,
                "generating_agent_cannot_be_the_independent_reviewer": True,
                "capstone_evidence_may_reuse_prerequisite_evidence": False,
            }
            and len(capstone_criteria) == 9
            and [item.get("id") for item in capstone_criteria] == [f"CAPSTONE-{index:02d}" for index in range(1, 10)]
            and len({item.get("description") for item in capstone_criteria}) == 9
            and all(
                item.get("claim_scope") == "ai_stewardship_process_only"
                and item.get("required_evidence_combination", {}).get("distinct_evidence_item_ids") is True
                and len(item.get("required_evidence_combination", {}).get("all_of", [])) >= 2
                and set(item.get("required_evidence_combination", {}).get("all_of", [])) <= allowed_evidence
                for item in capstone_criteria
            ),
            "Orchestration capstone requires every Advanced safety domain, new independent evidence and nine distinct process-only criteria",
        )
        notice = capabilities.get("noncredential_notice", "").casefold()
        c.check(all(term in notice for term in ["licensure", "credentialing", "clinical competence", "procedure authorization", "authorization to practice"]), "Capability notice rejects professional credential and authority claims")
        eligibility = capabilities.get("eligibility", {})
        excluded = eligibility.get("excluded", [])
        synthetic_rule = eligibility.get("synthetic_evidence_rule", "").casefold()
        synthetic_rule_normalized = synthetic_rule.replace("-", " ")
        c.check(
            "preloaded_starter_or_system_generated_activity" in excluded
            and "private_wellbeing_relationship_financial_health_schedule_or_family_information_in_badge_evidence" in excluded
            and all(term in synthetic_rule_normalized for term in ["resident authored", "ai stewardship", "preloaded/system generated", "never", "clinical reasoning", "competence", "opened current public sources"]),
            "Capability evidence excludes preloaded/private-life content and narrowly admits resident-authored fictional AI-stewardship evidence",
        )
        c.check(capabilities.get("contextual_human_review_policy", {}).get("applies_to_all_levels") is True, "Contextual named-human review applies at every level")
        c.check(normalized_digest(capabilities) == CAPABILITY_DIGEST, "Capability configuration digest is frozen", normalized_digest(capabilities))
    if isinstance(sources, dict):
        entries = sources.get("entries", [])
        c.check(sources.get("schema") == "NAIO-MR-ROUNDS-SOURCE-RECOMMENDATION-REGISTRY-1" and sources.get("count") == 14, "Source registry identity and count are exact")
        c.check([item.get("id") for item in entries] == [f"MR-SRC-{i:02d}" for i in range(1, 15)], "Source registry is exact MR-SRC-01..14")
        c.check(
            all(
                str(item.get("url", "")).startswith("https://")
                and item.get("canonical_source_captured_at") == "2026-07-20"
                and item.get("live_status") == "not_checked_by_build_kit"
                and item.get("refresh_required_at_install") is True
                and item.get("source_defined") is True
                for item in entries
            ),
            "All source recommendations retain canonical HTTPS URLs, frozen capture date, unverified live status and install-time refresh requirement",
        )
        c.check(all(item.get("source_path") == "source/rounds-domain-pack/core/02-ROUNDS-ATTEND-CIRCLE-ORBIT-Operating-Core.md" and item.get("source_file_sha256") == ROUNDS_TREE_HASHES["core/02-ROUNDS-ATTEND-CIRCLE-ORBIT-Operating-Core.md"] for item in entries), "Every source recommendation is path-and-hash pinned to the canonical operating core")
        c.check(sources.get("rules", {}).get("recommendation_grants_authority") is False and sources.get("rules", {}).get("unknown_id_behavior") == "reject", "Source recommendations grant no authority and reject unknown IDs")
        c.check(normalized_digest(sources) == SOURCE_REGISTRY_DIGEST, "Source recommendation registry digest is frozen", normalized_digest(sources))
    if isinstance(governance, dict):
        c.check(governance.get("schema") == "NAIO-MR-ROUNDS-GOVERNANCE-POLICY-1", "Governance schema identity is exact")
        c.check(set(governance.get("data_classes", {})) == set(DATA_CLASS_IDS) and len(governance.get("data_classes", {})) == len(DATA_CLASS_IDS), "Governance data classes are exact MR-DATA-0/1/2/W/M/P/A/R/C/E/S/X")
        c.check(
            governance.get("admitted_data_classes") == PERSONAL_ADMITTED_DATA_CLASSES
            and governance.get("institutional_declared_unavailable") == INSTITUTIONAL_DECLARED_UNAVAILABLE
            and governance.get("prohibited_data_classes") == PROHIBITED_DATA_CLASSES,
            "Governance personal admission, unavailable institutional and rejection sets are exact",
        )
        c.check(
            governance.get("processing_eligibility") == {
                "local_storage_eligible_after_admission": PERSONAL_ADMITTED_DATA_CLASSES,
                "model_prompt_eligible_after_exact_consent_and_task_screen": ["MR-DATA-0", "MR-DATA-1", "MR-DATA-2"],
                "agent_payload_eligible_subject_to_each_agent_contract": ["MR-DATA-0", "MR-DATA-1", "MR-DATA-2"],
                "manual_local_only_never_model_agent_tool_or_provider": ["MR-DATA-W"],
                "local_control_metadata_never_prompt_or_agent_payload": ["MR-DATA-M", "MR-DATA-R"],
                "declared_but_unavailable": INSTITUTIONAL_DECLARED_UNAVAILABLE,
                "rejected_before_echo_or_processing": PROHIBITED_DATA_CLASSES,
            },
            "Governance narrows model/agent payloads to 0/1/2, keeps W manual-local, and keeps M/R local control metadata only",
        )
        partitions = governance.get("partitions", {})
        c.check(
            partitions.get("personal_available") == PRIVATE_PARTITIONS
            and partitions.get("institutional_declared_unavailable") == INSTITUTIONAL_PARTITIONS
            and all(term in partitions.get("rule", "").casefold() for term in ["no route", "store", "toggle", "import", "bind", "connector", "transition"]),
            "Governance enumerates exact 3 personal and 6 technically unavailable institutional partitions",
        )
        edena = governance.get("edena", {})
        c.check(edena.get("independent_fields") == ["edena_tier", "absolute_stop"] and "cannot be waived" in edena.get("absolute_stop", "").casefold(), "EDENA tier and absolute stop are independent and nonwaivable")
        lifecycle = governance.get("execution", {}).get("artifact_lifecycle")
        c.check(lifecycle == ["Exploration", "Simulation", "Recommendation", "Draft Artifact", "Approved Plan", "Authorized Execution", "Completed Action", "Evaluated Outcome"], "Artifact lifecycle is exact")
        absolute = " ".join(governance.get("absolute_stop_categories", [])).casefold()
        c.check(all(term in absolute for term in ["patient", "prescribing", "credential", "ranking", "supervision", "illegal"]), "Absolute-stop catalog covers patient, prescribing, evaluation/authority, secret and illegal action")
        execution = governance.get("execution", {})
        execution_text = execution.get("authorized_execution", "").casefold()
        c.check(execution.get("personal_p4_available") is False and execution.get("institutional_context_provisioned") is False and execution.get("clinical_executor") is False and all(term in execution_text for term in ["external accountable human", "outside this package", "cannot be enabled"]), "Governance freezes external human execution, unavailable P4 and no clinical executor")
        c.check(
            execution.get("artifact_lifecycle_reachable_in_target") == ARTIFACT_LIFECYCLE_REACHABLE
            and execution.get("artifact_lifecycle_unreachable_reference_only") == ARTIFACT_LIFECYCLE_UNREACHABLE
            and execution.get("executor_shipped") is False
            and execution.get("clinical_executor") is False
            and execution.get("external_action_lifecycle_reference_only") is True
            and execution.get("external_action_transitions_available_in_target") == []
            and all(term in execution.get("completed_action", "").casefold() for term in ["unreachable", "cannot verify", "resident-reported_external_status_unverified"]),
            "Governance makes Authorized Execution, Completed Action and Evaluated Outcome unreachable and ships no executor or transition",
        )
        c.check(
            execution.get("orbit_lifecycle") == ORBIT_LIFECYCLE
            and execution.get("orbit_personal_reachable_states") == ORBIT_PERSONAL_REACHABLE
            and execution.get("orbit_personal_unreachable_reference_only_states") == ORBIT_PERSONAL_UNREACHABLE
            and execution.get("orbit_personal_forward_transition") == ORBIT_PERSONAL_FORWARD
            and execution.get("orbit_personal_early_termination") == ORBIT_PERSONAL_EARLY_TERMINATION,
            "Governance freezes the exact personal ORBIT path and makes Human-Released unreachable reference vocabulary",
        )
        catalog_mrref = catalog.get("reconciliation_reference_contract") if isinstance(catalog, dict) else None
        c.check(
            execution.get("reconciliation_reference_contract") == MRREF_CONTRACT
            and catalog_mrref == MRREF_CONTRACT,
            "Catalog and governance carry one exact local, nonresolving, nonofficial MRREF contract that cannot advance lifecycle",
        )
        c.check(
            governance.get("readiness_gate") == {
                "total_execution_records": 424,
                "live_backend_only_records": LIVE_BACKEND_ONLY_RECORD_IDS,
                "operational": {
                    "required": ["424_of_424_reconciled", "zero_not_run", "zero_failed", "zero_blocked", "genuine_authenticated_incremental_streaming_passed", "server_work_cancellation_passed"],
                },
                "core_operational_ai_setup_pending": {
                    "required": ["424_of_424_reconciled", "zero_not_run", "zero_failed", "zero_blocked_outside_live_backend_only_records", "controlled_unconfigured_ai_path_passed"],
                    "blocked_rows_must_equal_subset_of_live_backend_only_records": True,
                    "only_allowed_block_reason": "absent_configured_backend_after_controlled_unconfigured_path_passed",
                },
                "not_operational": "Any unmet predicate, any extra Blocked row, any Failed row, any Not Run row, or any blocker reason other than the exact absent-configured-backend condition.",
                "not_applicable_allowed": False,
            },
            "Readiness gate requires exact 424-row reconciliation and limits backend-absence blocking to seven named records",
        )
    if isinstance(professional, dict):
        c.check(professional.get("schema") == "NAIO-MR-ROUNDS-RESIDENT-SCHEMA-REGISTRY-1" and professional.get("namespace") == NAMESPACE and professional.get("count") == 17, "Resident schema registry identity, namespace and count are exact")
        professional_entries = professional.get("entries", [])
        c.check([item.get("id") for item in professional_entries] == RECORD_SCHEMAS and all(item.get("installation_state") == "declared_record_contract_not_operational" for item in professional_entries), "Resident registry preserves all seventeen canonical record IDs as declared non-operational contracts")
        required_contract_fields = professional.get("entry_contract_required_fields", [])
        expected_required_fields = [
            "purpose", "personal_available", "personal_availability", "allowed_record_scopes",
            "allowed_partitions", "allowed_data_classes", "prohibited_content", "prohibited_actions",
            "no_authority_effect", "authority_effect", "source_path", "source_file_sha256",
            "source_record_type_status", "machine_contract_status", "source_hash_status", "installation_state",
        ]
        exact_records = required_contract_fields == expected_required_fields and len(professional_entries) == 17
        for entry in professional_entries:
            record_id = entry.get("id")
            expected = RECORD_CONTRACT_EXPECTATIONS.get(record_id)
            if expected is None:
                exact_records = False
                continue
            scopes, partitions, data_classes, source_relative, extra_content, extra_actions = expected
            exact_records &= entry.get("declared_record_type") == record_id
            exact_records &= entry.get("personal_available") is True
            exact_records &= entry.get("allowed_record_scopes") == scopes
            exact_records &= entry.get("allowed_partitions") == partitions
            exact_records &= entry.get("allowed_data_classes") == data_classes
            exact_records &= entry.get("prohibited_content") == RECORD_BASE_PROHIBITED_CONTENT + extra_content
            exact_records &= entry.get("prohibited_actions") == RECORD_BASE_PROHIBITED_ACTIONS + extra_actions
            exact_records &= entry.get("no_authority_effect") is True
            exact_records &= entry.get("authority_effect") == "none; creating, editing, reviewing or approving this record cannot grant clinical authority, supervision, competence, credentials, privilege, institutional approval or permission to act"
            exact_records &= entry.get("source_path") == f"source/rounds-domain-pack/{source_relative}"
            exact_records &= entry.get("source_file_sha256") == ROUNDS_TREE_HASHES[source_relative]
            exact_records &= entry.get("source_record_type_status") == "source_declared_logical_record_type"
            exact_records &= entry.get("machine_contract_status") == "implementation_generated_restrictive_contract"
            exact_records &= entry.get("source_hash_status") == "pinned_expected_sha256_verify_at_install"
            exact_records &= set(required_contract_fields) <= set(entry)
        c.check(exact_records, "All seventeen record types carry exact scope, partition, data, prohibition, source-pin and no-authority machine contracts")
        rule = professional.get("partition_rule", "").casefold()
        c.check("same authorized medical-resident lane and partition" in rule and "five departments are record scopes" in rule and "whole-life" in rule and "unavailable" in rule, "Resident registry freezes same-partition references, one-home scopes and whole-life isolation")
    return catalog, agents, capabilities, sources, governance


def check_schemas(c: Checks, package: Path) -> None:
    pairs = [
        ("ROUNDS-Discover-Packet.schema.json", "ROUNDS-Discover-Packet.synthetic.example.json", "NAIO-MR-DISCOVER-PACKET-ADAPTER-1"),
        ("ROUNDS-Soul-Profile.schema.json", "ROUNDS-Soul-Profile.synthetic.example.json", "NAIO-MR-SOUL-PROFILE-ADAPTER-1"),
        ("ROUNDS-Mission-Profile.schema.json", "ROUNDS-Mission-Profile.synthetic.example.json", "NAIO-MR-ROUNDS-MISSION-PROFILE-1"),
    ]
    loaded: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for schema_name, fixture_name, identity in pairs:
        schema = load_json(c, package / "schemas" / schema_name, f"{schema_name} parses")
        fixture = load_json(c, package / "personalization" / fixture_name, f"{fixture_name} parses")
        if not isinstance(schema, dict) or not isinstance(fixture, dict):
            continue
        c.check(not unsupported_schema_keywords(schema), f"{schema_name} uses only enforced schema keywords", unsupported_schema_keywords(schema))
        c.check(schema.get("properties", {}).get("schema", {}).get("const") == identity and fixture.get("schema") == identity, f"{schema_name} freezes {identity}")
        errors = validate_json_schema(fixture, schema)
        c.check(not errors, f"{fixture_name} validates against its schema", errors[:10])
        c.check(fixture.get("demo") is True and "Synthetic" in fixture.get("display_name", "Synthetic") if "display_name" in fixture else fixture.get("demo") is True, f"{fixture_name} is unmistakably synthetic")
        unknown = dict(fixture)
        unknown["raw_answers"] = ["must be rejected"]
        c.check(bool(validate_json_schema(unknown, schema)), f"{schema_name} rejects raw answers and unknown fields")
        loaded[schema_name] = (schema, fixture)
    # Prove engine behavior independently of the bundled schemas.
    c.check(bool(validate_json_schema({"x": 1}, {"type": "object", "not": {"required": ["x"]}})), "Schema engine enforces not with strict numeric equality")
    c.check(not validate_json_schema(["a", "b"], {"type": "array", "prefixItems": [{"const": "a"}, {"const": "b"}], "items": False}) and bool(validate_json_schema(["a", "b", "c"], {"type": "array", "prefixItems": [{"const": "a"}, {"const": "b"}], "items": False})), "Schema engine enforces prefixItems and Boolean items false")
    c.check(bool(validate_json_schema(True, {"const": 1})), "Schema engine does not treat Boolean true as numeric 1")
    c.check(bool(validate_json_schema("not-a-uuid", {"type": "string", "format": "uuid"})), "Schema engine enforces UUID format")
    c.check(bool(validate_json_schema("2026-01-01T12:00:00", {"type": "string", "format": "date-time"})), "Schema engine enforces offset date-time format")
    discover_pair = loaded.get("ROUNDS-Discover-Packet.schema.json")
    if discover_pair:
        discover_schema, discover = discover_pair
        c.check(
            discover.get("resident_status") in ROLE_STATUSES
            and set(discover.get("role_adapters", [])).issubset(ROLE_ADAPTERS)
            and set(discover.get("task_hats", [])).issubset(TASK_HATS)
            and discover.get("ai_boundaries") == {
                "default_support": "prepare_only", "external_actions": "off", "memory_default": "session_only",
                "never_delegate": ["patient care", "supervision decisions", "prescribing", "credential or competence claims", "formal evaluation"],
            },
            "Synthetic Discover adapter freezes resident roles, hats and no-delegation boundaries",
        )
        bad_discover = json.loads(json.dumps(discover)); bad_discover["role_adapters"] = ["nurse_practitioner"]
        authority_discover = json.loads(json.dumps(discover)); authority_discover["verified_supervision"] = True
        c.check(bool(validate_json_schema(bad_discover, discover_schema)) and bool(validate_json_schema(authority_discover, discover_schema)), "Discover schema rejects cross-population and authority-inflating inputs")
    soul_pair = loaded.get("ROUNDS-Soul-Profile.schema.json")
    if soul_pair:
        soul_schema, soul = soul_pair
        c.check(
            soul.get("ai_permission_preferences") == {"agents": "disabled_until_one_run_approval", "external_actions": "off", "maximum_model_permission": "P2", "tools": "disabled_until_one_run_approval"}
            and soul.get("memory_preferences", {}).get("default") == "session_only"
            and all(term in " ".join(soul.get("nonnegotiable_boundaries", [])).casefold() for term in ["patient", "live-care", "authority", "evaluation"]),
            "Synthetic Soul adapter freezes P2, session-only memory and nonnegotiable resident boundaries",
        )
        bad_soul = json.loads(json.dumps(soul)); bad_soul["ai_permission_preferences"]["maximum_model_permission"] = "P3"
        raw_soul = json.loads(json.dumps(soul)); raw_soul["raw_soul_md"] = "must never be admitted"
        c.check(bool(validate_json_schema(bad_soul, soul_schema)) and bool(validate_json_schema(raw_soul, soul_schema)), "Soul schema rejects permission inflation and raw identity material")
    mission_pair = loaded.get("ROUNDS-Mission-Profile.schema.json")
    if mission_pair:
        schema, fixture = mission_pair
        clone = lambda value: json.loads(json.dumps(value))
        properties = schema.get("properties", {})
        c.check(
            properties.get("resident_status", {}).get("enum") == ROLE_STATUSES
            and properties.get("primary_role_adapter", {}).get("enum") == ROLE_ADAPTERS
            and properties.get("role_adapters", {}).get("items", {}).get("enum") == ROLE_ADAPTERS
            and properties.get("task_hats", {}).get("items", {}).get("enum") == TASK_HATS
            and properties.get("primary_task_hat", {}).get("enum") == TASK_HATS,
            "Mission schema freezes exact 6 resident statuses, 5 role adapters and 11 task hats",
        )
        c.check(
            fixture.get("product_id") == PRODUCT_ID
            and fixture.get("lane") == LANE
            and fixture.get("foundation_namespace") == FOUNDATION_NAMESPACE
            and fixture.get("namespace") == NAMESPACE
            and fixture.get("canonical_route") == ROUTE,
            "Synthetic Mission Profile target identity and namespace are exact",
        )
        c.check(
            fixture.get("resident_status") in ROLE_STATUSES
            and fixture.get("primary_role_adapter") in ROLE_ADAPTERS
            and set(fixture.get("role_adapters", [])).issubset(ROLE_ADAPTERS)
            and fixture.get("active_partition") in PRIVATE_PARTITIONS,
            "Synthetic profile has an exact resident role adapter and private partition",
        )
        scopes = fixture.get("record_scopes", [])
        c.check(
            [(item.get("id"), item.get("title")) for item in scopes] == WORKSPACES
            and len([item for item in scopes if item.get("active")]) == 1
            and next(item["id"] for item in scopes if item.get("active")) == fixture.get("active_record_scope_id"),
            "Synthetic Mission Profile instantiates five exact record scopes with one active",
        )
        c.check(
            fixture.get("active_deployment_context") == "private_resident_os"
            and fixture.get("institutional_context_available") is False
            and fixture.get("institutional_context_requires_separate_runtime_bind") is True
            and fixture.get("institutional_runtime_bind") is None
            and fixture.get("whole_life_available") is True,
            "Synthetic Mission Profile is technically personal-only with no institutional bind",
        )
        expected_attend = {
            "activity_active_hat", "training_task_entrustment", "team_attending",
            "environment_evidence_data", "need_for_escalation", "decision_documentation_destination",
        }
        attend = fixture.get("supervision_context", {})
        c.check(
            set(attend) == expected_attend
            and all(item.get("state") == "verification_needed" and all(item.get(key) is None for key in ["source_ref", "source_version", "human_owner_role", "verified_at", "effective_at", "expires_at"]) for item in attend.values())
            and fixture.get("supervision_state") == "unverified",
            "Synthetic ATTEND context has six exact gates and no borrowed verification",
        )
        temporal_rules = [
            "effective_at <= verified_at < expires_at for source_linked and resident_recorded_human_confirmation",
            "expires_at must be later than the runtime evaluation time for consequential use",
            "missing, inverted, stale or expired dates force gate state verification_needed and aggregate supervision_state unverified",
        ]
        gate_schemas = properties.get("supervision_context", {}).get("properties", {})
        c.check(
            set(gate_schemas) == expected_attend
            and all(item.get("x-runtime-temporal-constraints") == temporal_rules for item in gate_schemas.values()),
            "Every ATTEND gate declares the exact ordered-date, live-expiry and stale-to-unverified runtime rules",
        )
        attend_nonnull_fields = ["source_ref", "source_version", "effective_at", "verified_at", "expires_at", "human_owner_role"]
        valid_attend_values = {
            "source_ref": "MR-SRC-01", "source_version": "2026-current-owner-verified",
            "effective_at": "2026-07-20T08:00:00-07:00", "verified_at": "2026-07-20T09:00:00-07:00",
            "expires_at": "2026-07-21T09:00:00-07:00", "human_owner_role": "authorized program human",
        }
        attend_state_bases: dict[str, Any] = {}
        for state in ["source_linked", "resident_recorded_human_confirmation"]:
            candidate = clone(fixture)
            candidate["supervision_context"]["team_attending"] = {"state": state, **valid_attend_values}
            attend_state_bases[state] = candidate
        c.check(
            all(not validate_json_schema(candidate, schema) for candidate in attend_state_bases.values()),
            "ATTEND source-linked and resident-recorded human-confirmation states accept a complete six-field provenance set",
        )
        null_mutations: list[tuple[str, list[str]]] = []
        for state, base in attend_state_bases.items():
            for field in attend_nonnull_fields:
                candidate = clone(base)
                candidate["supervision_context"]["team_attending"][field] = None
                null_mutations.append((f"{state}:{field}", validate_json_schema(candidate, schema)))
        c.check(
            len(null_mutations) == 12 and all(errors for _, errors in null_mutations),
            "ATTEND rejects null source, version, effective, verified, expiry and owner for both consequential linked states",
            [label for label, errors in null_mutations if not errors],
        )
        provenance = fixture.get("field_provenance", [])
        c.check(
            [item.get("field") for item in provenance] == PROFILE_PROVENANCE_FIELDS
            and len({item.get("field") for item in provenance}) == len(PROFILE_PROVENANCE_FIELDS)
            and all(item.get("approval") == "proposed" for item in provenance),
            "Every proposed profile field has exactly one proposed provenance row",
        )
        def system_default_provenance_valid(profile: dict[str, Any]) -> bool:
            if not SYSTEM_PROFILE_FIELDS <= set(profile):
                return False
            source = {
                "schema": "NAIO-MR-ROUNDS-MISSION-PROFILE-SYSTEM-DEFAULT-SOURCE-1",
                "version": "1.0-draft",
                "fields": {field: profile[field] for field in sorted(SYSTEM_PROFILE_FIELDS)},
            }
            expected_hash = canonical_record_digest(source)
            expected_fields = [field for field in PROFILE_PROVENANCE_FIELDS if field in SYSTEM_PROFILE_FIELDS]
            rows = [item for item in profile.get("field_provenance", []) if item.get("source") == "system_default"]
            return (
                [item.get("field") for item in rows] == expected_fields
                and all(
                    item.get("source_record_hash") == expected_hash
                    and item.get("source_record_hash_algorithm") == "sha256_sorted_canonical_json_utf8"
                    and item.get("source_adapter_schema") == "NAIO-MR-ROUNDS-MISSION-PROFILE-1"
                    and item.get("source_adapter_version") == "1.0-draft"
                    and item.get("source_value_stored") is False
                    for item in rows
                )
            )
        tampered_system_default = clone(fixture)
        tampered_system_default["ai_preferences"]["default_support"] = "suggest_only"
        c.check(
            system_default_provenance_valid(fixture)
            and not validate_json_schema(tampered_system_default, schema)
            and not system_default_provenance_valid(tampered_system_default),
            "System-default provenance hash binds the complete actual field object and detects a schema-valid nested-field tamper",
        )
        rec = fixture.get("recommended_assets", {})
        c.check(
            [item.get("id") for item in rec.get("powers", [])] == [f"PWR-{i:02d}" for i in range(1, 25)]
            and all(item.get("state") == "available_inactive" for item in rec.get("powers", []))
            and [item.get("id") for item in rec.get("workflows", [])] == [f"WF-{i:02d}" for i in range(1, 25)]
            and all(item.get("state") == "preview_only" for item in rec.get("workflows", []))
            and rec.get("templates") == [f"TPL-{i:02d}" for i in range(1, 31)]
            and [item.get("id") for item in rec.get("agents", [])] == [item[0] for item in AGENTS]
            and all(item.get("permission") == "PERM-P0 Disabled" for item in rec.get("agents", []))
            and rec.get("source_recommendations") == [f"MR-SRC-{i:02d}" for i in range(1, 15)],
            "Synthetic recommendations contain exact ordered 24/24/30/10/14 assets",
        )
        c.check(
            fixture.get("ai_preferences") == {
                "agent_permission_state": "PERM-P0 Disabled", "agent_state": "disabled",
                "background_automation": "off", "default_support": "prepare_only",
                "external_actions": "off", "maximum_personal_permission": "P2",
                "p3_available": False, "p4_available": False, "tools": "disabled",
            },
            "Synthetic AI state is P0 with P3/P4, tools, background work and execution off",
        )
        boundary = fixture.get("data_boundary", {})
        c.check(
            boundary.get("personal_admitted") == PERSONAL_ADMITTED_DATA_CLASSES
            and boundary.get("model_prompt_eligible") == ["MR-DATA-0", "MR-DATA-1", "MR-DATA-2"]
            and boundary.get("agent_payload_eligible") == ["MR-DATA-0", "MR-DATA-1", "MR-DATA-2"]
            and boundary.get("manual_local_only") == ["MR-DATA-W"]
            and boundary.get("local_control_metadata_only") == ["MR-DATA-M", "MR-DATA-R"]
            and boundary.get("institutional_declared_unavailable") == INSTITUTIONAL_DECLARED_UNAVAILABLE
            and boundary.get("rejected_before_echo_and_persistence") == PROHIBITED_DATA_CLASSES
            and not set(boundary.get("personal_admitted", [])) & set(PROHIBITED_DATA_CLASSES),
            "Synthetic profile freezes local admission, 0/1/2 payload eligibility, W manual-only, M/R control-only and prohibited-class rejection",
        )
        c.check(all(value is True for value in fixture.get("practice_boundaries", {}).values()), "Every synthetic resident practice boundary is enabled")

        adversarial: list[tuple[str, Any]] = []
        candidate = clone(fixture); candidate["canonical_route"] = "/wrong"; adversarial.append(("wrong route", candidate))
        candidate = clone(fixture); candidate["profile_id"] = "not-a-uuid"; adversarial.append(("malformed UUID", candidate))
        candidate = clone(fixture); candidate["record_scopes"][0], candidate["record_scopes"][1] = candidate["record_scopes"][1], candidate["record_scopes"][0]; adversarial.append(("record-scope reordering", candidate))
        candidate = clone(fixture); [item.update({"active": False}) for item in candidate["record_scopes"]]; adversarial.append(("zero active record scopes", candidate))
        candidate = clone(fixture); candidate["record_scopes"][0]["active"] = True; adversarial.append(("multiple active record scopes", candidate))
        candidate = clone(fixture); candidate["active_record_scope_id"] = WORKSPACES[0][0]; adversarial.append(("active-scope mismatch", candidate))
        candidate = clone(fixture); candidate["primary_task_hat"] = next(item for item in TASK_HATS if item not in candidate["task_hats"]); adversarial.append(("primary hat absent from selected hats", candidate))
        candidate = clone(fixture); candidate["secondary_task_hat"] = candidate["primary_task_hat"]; adversarial.append(("duplicate primary and secondary hats", candidate))
        candidate = clone(fixture); candidate["primary_role_adapter"] = next(item for item in ROLE_ADAPTERS if item not in candidate["role_adapters"]); adversarial.append(("primary role adapter absent from selected adapters", candidate))
        candidate = clone(fixture); candidate["active_deployment_context"] = "institution_approved_resident_workspace"; adversarial.append(("institutional context activation", candidate))
        candidate = clone(fixture); candidate["institutional_context_available"] = True; adversarial.append(("institutional context availability", candidate))
        candidate = clone(fixture); candidate["institutional_runtime_bind"] = {"status": "claimed"}; adversarial.append(("institutional runtime bind", candidate))
        candidate = clone(fixture); candidate["active_partition"] = "institution_clinical"; adversarial.append(("institutional partition", candidate))
        candidate = clone(fixture); candidate["governance_preferences"]["edition"] = "institutional_managed"; adversarial.append(("institutional governance edition", candidate))
        candidate = clone(fixture); candidate["ai_preferences"]["p3_available"] = True; adversarial.append(("P3 availability in personal target", candidate))
        candidate = clone(fixture); candidate["ai_preferences"]["p4_available"] = True; adversarial.append(("P4 availability in personal target", candidate))
        candidate = clone(fixture); candidate["ai_preferences"]["agent_permission_state"] = "PERM-P1 Private Nonsensitive or Synthetic Draft"; adversarial.append(("non-P0 default agent state", candidate))
        candidate = clone(fixture); candidate["practice_boundaries"]["no_live_patient_care"] = False; adversarial.append(("disabled patient-care boundary", candidate))
        candidate = clone(fixture); candidate["data_boundary"]["personal_admitted"].append("MR-DATA-C"); adversarial.append(("patient class admission", candidate))
        candidate = clone(fixture); candidate["data_boundary"]["personal_admitted"].append("MR-DATA-E"); adversarial.append(("formal-evaluation class admission", candidate))
        candidate = clone(fixture); candidate["data_boundary"]["model_prompt_eligible"].append("MR-DATA-W"); adversarial.append(("whole-life model-prompt eligibility", candidate))
        candidate = clone(fixture); candidate["data_boundary"]["agent_payload_eligible"].append("MR-DATA-M"); adversarial.append(("control metadata agent-payload eligibility", candidate))
        candidate = clone(fixture); candidate["data_boundary"]["manual_local_only"] = []; adversarial.append(("omitted manual-local whole-life boundary", candidate))
        candidate = clone(fixture); candidate["data_boundary"]["local_control_metadata_only"] = ["MR-DATA-R", "MR-DATA-M"]; adversarial.append(("reordered control-metadata-only boundary", candidate))
        candidate = clone(fixture); candidate["data_boundary"]["institutional_declared_unavailable"] = []; adversarial.append(("omitted unavailable institutional data classes", candidate))
        candidate = clone(fixture); gate = candidate["supervision_context"]["team_attending"]; gate["state"] = "resident_recorded_human_confirmation"; adversarial.append(("claimed supervision without provenance", candidate))
        candidate = clone(fixture); candidate["supervision_state"] = "resident_recorded_human_confirmation"; adversarial.append(("aggregate supervision claim with unverified gates", candidate))
        candidate = clone(fixture); candidate["active_partition"] = "whole_life_private"; adversarial.append(("whole-life partition outside the Role, Duty & Life scope", candidate))
        candidate = clone(fixture); candidate["field_provenance"] = candidate["field_provenance"][:-1]; adversarial.append(("missing provenance row", candidate))
        candidate = clone(fixture); candidate["field_provenance"][0]["field"] = candidate["field_provenance"][1]["field"]; adversarial.append(("duplicate provenance field", candidate))
        for asset_name in ["powers", "workflows", "templates", "agents", "source_recommendations"]:
            candidate = clone(fixture); candidate["recommended_assets"][asset_name] = candidate["recommended_assets"][asset_name][:-1]; adversarial.append((f"incomplete {asset_name}", candidate))
        rejected = [(label, validate_json_schema(candidate, schema)) for label, candidate in adversarial]
        c.check(all(errors for _, errors in rejected), "Mission schema rejects every adversarial authority, context, safety, provenance and inventory mutation", [label for label, errors in rejected if not errors])


def check_test_inventories(c: Checks, package: Path) -> dict[str, Any]:
    path = package / "implementation/MR-Control-Completeness-Matrix.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        matrix = list(reader)
        columns = tuple(reader.fieldnames or ())
    c.check(columns == EXPECTED_MATRIX_COLUMNS, "Control matrix has the exact 11-column contract", columns)
    c.check(len(matrix) == EXPECTED_MATRIX_ROWS, "Control matrix has exactly 216 rows", len(matrix))
    ids = [row.get("control_id", "") for row in matrix]
    c.check(len(set(ids)) == EXPECTED_MATRIX_ROWS and all(re.fullmatch(r"[A-Z][A-Z0-9_]{1,15}-[0-9]{3}", item) for item in ids), "Control IDs are unique and well formed")
    c.check([row.get("control") for row in matrix if row.get("control_id", "").startswith("PWR-")] == POWERS, "PWR controls map one-to-one to the twenty-four ROUNDS powers")
    c.check([row.get("control") for row in matrix if row.get("control_id", "").startswith("WF-")] == WORKFLOWS, "WF controls map one-to-one to the twenty-four workflows")
    c.check(all(str(row.get(column, "")).strip() for row in matrix for column in EXPECTED_MATRIX_COLUMNS), "Control matrix has no empty required cell")
    c.check({row.get("status") for row in matrix} == {"Not Run"}, "Every control matrix row starts Not Run")
    exact_control_contracts = True
    critical_contracts = True
    verification_tests: list[str] = []
    group_signatures: set[tuple[str, str, str, str]] = set()
    for row in matrix:
        control_id = row.get("control_id", "")
        prefix = control_id.split("-", 1)[0]
        title = row.get("control", "")
        profile = CONTROL_GROUP_CONTRACTS.get(prefix)
        if profile is None:
            exact_control_contracts = False
            continue
        target, permission, persisted, negative_fixture, expected_state = profile
        expected_verification = (
            f"{control_id}: exercise the valid `{title}` path and inspect its state; then run {negative_fixture}. "
            f"Required result: {expected_state}. Capture executable trace, state/database or zero-residue inspection, "
            "restart/replay result where applicable, and evidence path."
        )
        exact_control_contracts &= row.get("implementation_target") == target
        exact_control_contracts &= row.get("required_permission") == permission
        exact_control_contracts &= row.get("persisted_data") == f"For `{title}`: {persisted}."
        exact_control_contracts &= row.get("verification_test") == expected_verification
        verification_tests.append(row.get("verification_test", ""))
        group_signatures.add((target, permission, negative_fixture, expected_state))
        if prefix in CRITICAL_CONTROL_GROUPS:
            critical_contracts &= control_id in row.get("verification_test", "")
            critical_contracts &= f"`{title}`" in row.get("verification_test", "")
            critical_contracts &= "exercise the valid" in row.get("verification_test", "")
            critical_contracts &= negative_fixture in row.get("verification_test", "")
            critical_contracts &= expected_state in row.get("verification_test", "")
            critical_contracts &= row.get("required_permission") == permission
            critical_contracts &= all(
                term in row.get("verification_test", "")
                for term in ["state/database or zero-residue inspection", "restart/replay", "evidence path"]
            )
    c.check(set(item.split("-", 1)[0] for item in ids) == set(CONTROL_GROUP_CONTRACTS), "Control matrix has only the exact seventeen named control groups")
    c.check(exact_control_contracts, "Every matrix row has its exact group-specific target, permission, persistence, valid path, negative fixture, transition result and evidence contract")
    c.check(critical_contracts, "Every Critical control has a named control, group-specific valid/negative fixture, expected transition, persistence/zero-residue rule, permission and evidence path")
    c.check(
        len(verification_tests) == len(set(verification_tests)) == EXPECTED_MATRIX_ROWS
        and len(group_signatures) == len(CONTROL_GROUP_CONTRACTS),
        "Control verification tests reject exact template duplication and preserve a distinct group contract for every control family",
    )
    ledger = markdown_table_rows((package / "implementation/MR-Acceptance-and-Test-Ledger.md").read_text(encoding="utf-8"))
    c.check(
        ledger.count(list(EXPECTED_CONTROL_LEDGER_COLUMNS)) == 1
        and ledger.count(list(EXPECTED_INTEGRATION_LEDGER_COLUMNS)) == 1
        and ledger.count(list(EXPECTED_CANONICAL_LEDGER_COLUMNS)) == 1,
        "Acceptance ledger has exact control, integration and eleven-column canonical headers",
    )
    ctl = [row for row in ledger if row and row[0].startswith("CTL-")]
    integration = [row for row in ledger if row and re.fullmatch(r"INT-[0-9]{3}", row[0])]
    canonical = [row for row in ledger if row and re.fullmatch(r"(?:[A-R][1-8]|INT(?:0[1-9]|1[0-6]))", row[0])]
    ctl_exact = [row[0] for row in ctl] == [f"CTL-{item}" for item in ids]
    if ctl_exact:
        for row, matrix_row in zip(ctl, matrix):
            expected_priority = "Critical" if matrix_row["control_id"].split("-", 1)[0] in CRITICAL_CONTROL_GROUPS else "Required"
            ctl_exact &= row == [
                f"CTL-{matrix_row['control_id']}", matrix_row["screen"], expected_priority,
                matrix_row["verification_test"], "Executable result, state inspection and evidence path", "Not Run",
            ]
    c.check(ctl_exact, "CTL ledger exactly mirrors every matrix target, Critical/Required priority, evidence contract and Not Run state")
    c.check([row[0] for row in integration] == [f"INT-{i:03d}" for i in range(1, 49)] and all(len(row) == 6 and row[-1] == "Not Run" for row in integration), "Integration ledger has exact INT-001..048 Not Run rows")
    c.check(len({row[3] for row in integration}) == 48 and len({row[4] for row in integration}) == 48 and all(len(row[3]) >= 80 and len(row[4]) >= 60 for row in integration), "Every integration scenario has a distinct specific expected result and evidence contract")
    c.check(
        len(integration) == 48
        and integration[28] == [
            "INT-029",
            "Private fatigue, wellbeing and whole-life processing/export denial",
            "Critical",
            "Program or employer requests cannot export private fatigue, health, recovery, family, finance or purpose data. MR-DATA-W remains manual/local only and is rejected from every model, provider, agent and tool path.",
            "MR-DATA-W canary fixtures through prompt, chat, provider, agent, tool, search/log and export entry points; zero provider/agent/tool calls; zero prompt/log residue; program/employer analytics and export zero-field disclosure; deletion check.",
            "Not Run",
        ],
        "INT-029 exactly proves MR-DATA-W provider, agent, tool, prompt, log, analytics and export denial",
    )
    all_target_ids = {row[0] for row in ctl + integration}
    c.check(
        LIVE_BACKEND_ONLY_RECORD_IDS == ["CTL-AI-002", "CTL-AI-003", "CTL-AI-004", "CTL-AI-005", "CTL-AI-006", "CTL-AI-007", "INT-044"]
        and set(LIVE_BACKEND_ONLY_RECORD_IDS) <= all_target_ids,
        "Only CTL-AI-002..007 and INT-044 are named live-backend-only records, and all seven exist",
    )
    canonical_sets = [CANONICAL_INSTITUTION_ONLY_IDS, CANONICAL_MIXED_IDS, CANONICAL_NEGATIVE_IDS]
    c.check(
        not any(canonical_sets[left] & canonical_sets[right] for left in range(3) for right in range(left + 1, 3))
        and set().union(*canonical_sets) <= set(expected_canonical_ids())
        and {"B4", "E1", "J1", "N3"} <= CANONICAL_MIXED_IDS
        and "G7" in CANONICAL_INSTITUTION_ONLY_IDS
        and set(CANONICAL_SPECIAL_PROOFS) == {"E8", "F5", "G1", "G3", "G4", "G5", "G7", "L6", "Q6", "INT05"},
        "Canonical institution-only, mixed and negative disposition maps are explicit, disjoint and carry all ten special proofs",
    )
    canonical_shape = [row[0] for row in canonical] == expected_canonical_ids() and all(len(row) == 11 and row[-1] == "Not Run" for row in canonical)
    c.check(canonical_shape, "Canonical ledger has exact A1..R8 plus INT01..16 order, eleven columns and Not Run states")
    canonical_semantics = canonical_shape
    if canonical_shape:
        for row in canonical:
            disposition, proof = canonical_target_disposition(row[0], row[2])
            canonical_semantics &= row == [
                row[0], row[1], row[2], f"`{disposition}`", proof, "Not recorded", CANONICAL_SOURCE_REFERENCE,
                CANONICAL_OWNER, "Not recorded", "Not recorded", "Not Run",
            ]
    c.check(canonical_semantics, "Every canonical row has the exact disposition, proof, evidence placeholder, source path/hash, owner, timestamp, remediation and Not Run result")
    source_rows = canonical_source_rows(package / CANONICAL_SOURCE_PATH)
    if source_rows:
        c.check(
            source_rows == [(row[0], row[1], row[2]) for row in canonical],
            "All 160 ledger priorities and source requirements exactly equal the hash-pinned canonical release-assurance source",
        )
    else:
        c.check(
            not (package / CANONICAL_SOURCE_PATH).exists(),
            "Canonical source comparison is deferred only for preassembly packages that do not yet carry immutable sources",
        )
    c.check(
        all(row[-1] == "Not Run" and all(cell != "Not applicable" for cell in row) for row in canonical)
        and "`Not applicable` is not permitted" in (package / "implementation/MR-Acceptance-and-Test-Ledger.md").read_text(encoding="utf-8"),
        "Canonical ledger permits no Not applicable result or waiver; institution-only requirements use executable absence tests",
    )
    c.check(len(ctl) + len(integration) == 264 and len(canonical) == 160, "Ledger counts are exactly 264 target and 160 canonical")
    text = (package / "implementation/MR-Acceptance-and-Test-Ledger.md").read_text(encoding="utf-8")
    c.check("Total required execution records: 424" in text, "Ledger states exact 216 + 48 + 160 = 424 accounting")
    values = {
        "control_id_digest": hashlib.sha256(("\n".join(ids) + "\n").encode()).hexdigest(),
        "matrix_semantic_digest": normalized_digest([[row[column] for column in EXPECTED_MATRIX_COLUMNS] for row in matrix]),
        "integration_semantic_digest": normalized_digest(integration),
    }
    c.check(values["control_id_digest"] == CONTROL_ID_DIGEST, "Control-ID digest is frozen", values["control_id_digest"])
    c.check(values["matrix_semantic_digest"] == MATRIX_SEMANTIC_DIGEST, "Control-matrix semantic digest is frozen", values["matrix_semantic_digest"])
    c.check(values["integration_semantic_digest"] == INTEGRATION_SEMANTIC_DIGEST, "Integration-scenario semantic digest is frozen", values["integration_semantic_digest"])
    return values


def check_core_docs(c: Checks, package: Path) -> None:
    build_status = (package / "BUILD-STATUS.md").read_text(encoding="utf-8")
    gap_report = (package / "implementation/MR-Baseline-Gap-Report.md").read_text(encoding="utf-8")
    give = (package / "GIVE-THIS-PACKAGE-TO-HERMES.md").read_text(encoding="utf-8")
    product = (package / "implementation/MR-Product-Specification.md").read_text(encoding="utf-8")
    governance = (package / "implementation/MR-Governance-EDENA-and-Data-Boundaries.md").read_text(encoding="utf-8")
    architecture = (package / "implementation/MR-Architecture-and-Data-Model.md").read_text(encoding="utf-8")
    guide = (package / "implementation/MR-Guide-Page-Content.md").read_text(encoding="utf-8")
    security = (package / "implementation/MR-Security-and-Privacy-Checklist.md").read_text(encoding="utf-8")
    agents = (package / "implementation/MR-Agent-Team-and-Routing.md").read_text(encoding="utf-8")
    technical = (package / "implementation/MR-Technical-Implementation-Guide.md").read_text(encoding="utf-8")
    resident_registry = (package / "config/MR-Professional-Schema-Registry.v1.json").read_text(encoding="utf-8")
    governance_registry = (package / "config/MR-Governance-Policy.v1.json").read_text(encoding="utf-8")
    mission_schema = (package / "schemas/ROUNDS-Mission-Profile.schema.json").read_text(encoding="utf-8")
    handoff = (package / "implementation/HERMES-FINAL-HANDOFF-REPORT-TEMPLATE.md").read_text(encoding="utf-8")
    precedence = (package / "INPUT-PRECEDENCE.md").read_text(encoding="utf-8")
    text = "\n".join([give, product, governance, architecture, guide, security, agents, technical, resident_registry, governance_registry, mission_schema, handoff]).casefold()
    normalized = text.replace("-", " ").replace("‑", " ")
    c.check(all(term.casefold() in text for term in [BUILD_ID, PRODUCT_ID, LANE, ROUTE, HOME, FOUNDATION_NAMESPACE, NAMESPACE]), "Core contracts document exact build identity")
    c.check(
        all(term in normalized for term in ["patient", "real case", "live care", "diagnosis", "treatment", "prescribing", "ordering", "coding", "billing", "claims"])
        and ("chart" in normalized or "charting" in normalized),
        "Core contracts document the patient and clinical-action boundary",
    )
    c.check(
        all(term in governance.casefold() for term in ["attend", "circle", "orbit", "activity and active hat", "training level and task entrustment", "team and attending", "environment, evidence, and data", "need for escalation", "decision, documentation, and destination", "unverified — authorized human confirmation required"]),
        "Governance documents exact six-gate ATTEND plus CIRCLE/ORBIT and verification truth",
    )
    c.check(
        all(term in governance.casefold() for term in ["edena", "independent", "absolute_stop", "new clean generic/fictional", "original payload is discarded", "institutional red remains blocked", "never waivable"]),
        "Governance documents independent EDENA, clean-slate Personal Red and nonwaivable stops",
    )
    c.check(
        all(
            term in product.casefold()
            for term in [
                "can reach no state after approved plan",
                "authorized execution, completed action, and evaluated outcome are reference-only labels",
                "no route, transition, connector, executor, imported attestation, or official-status store",
                "locally generated, content-free, nonresolving receipt id",
                "cannot prove or advance external completion",
                "resident-reported_external_status_unverified",
                "never changes lifecycle state",
            ]
        ),
        "Product contract makes every post-Approved-Plan state unreachable and MRREF nonofficial, nonresolving and non-advancing",
    )
    c.check(
        all(term in agents.casefold() for term in ["perm-p0 disabled", "p1", "p2", "p3 and p4", "technically unavailable", "p5", "prohibited", "zero hidden retries", "no recursion"]),
        "Agent contract documents P0 default, bounded P1/P2, unavailable P3/P4 and prohibited P5",
    )
    c.check(
        "mr-data-0/1/2/m/r" not in agents.casefold()
        and "mr-data-0/1/2` subsets" in agents.casefold()
        and all(term in agents.casefold() for term in ["mr-data-w", "manual/local only", "never sent to a model or agent"]),
        "Agent documentation limits payloads to 0/1/2 subsets and keeps W plus M/R outside model/agent payloads",
    )
    c.check(all(name.casefold() in resident_registry.casefold() for name in RECORD_SCHEMAS), "Core contracts enumerate all seventeen canonical resident-owned schemas")
    c.check(all(item.casefold() in mission_schema.casefold() for item in TASK_HATS), "Mission schema enumerates all eleven exact resident task hats")
    c.check(
        all(item.casefold() in text for item in PARTITIONS)
        and all(item.casefold() not in mission_schema.casefold() for item in INSTITUTIONAL_PARTITIONS),
        "Core contracts enumerate nine partitions while the personal Mission schema excludes all six institutional partitions",
    )
    c.check(all(item.casefold() in governance.casefold() for item in DATA_CLASS_IDS) and "whole-life" in governance.casefold() and "never badge" in governance.casefold(), "Governance documents all data classes and whole-life isolation")
    c.check(all(term in normalized for term in ["keyboard", "screen reader", "noncolor", "reduced motion", "plain"]), "Core contracts document accessibility and human-design boundaries")
    c.check(all(term in normalized for term in ["backup", "restore", "rollback", "rounds removal", "uninstall"]), "Core contracts document recovery boundaries")
    c.check(all(term in give for term in ["Implementation Activation Card", "Approve", "Revise", "Cancel", "S0", "S1", "S2", "S3", "S4"]), "Hermes handoff requires activation approval and phased checkpoint receipts")
    c.check(all(state in handoff for state in ["**Operational**", "**Core operational; AI setup pending**", "**Not operational**"]), "Handoff contains the three exact readiness states")
    c.check(
        all(
            term in handoff
            for term in [
                "424/424 reconciled", "zero Not Run, Failed, Blocked, or Not applicable",
                "genuine authenticated incremental streaming", "server-work cancellation",
                "zero Blocked rows outside `CTL-AI-002..007` plus `INT-044`",
                "absent_configured_backend_after_controlled_unconfigured_path_passed",
                "any unmet predicate, extra Blocked row, Failed/Not Run row, or different blocker reason",
            ]
        ),
        "Final handoff exposes the exact 424-record readiness predicates and sole seven-row backend exception",
    )
    precedence_lower = precedence.casefold()
    normative_handoff = "`give-this-package-to-hermes.md`, this precedence file, and the resolved `implementation/mr-functional-build-master-prompt.md`"
    normative_machine = "the machine contracts under `config/`, `schemas/`, `personalization/`, and `implementation/mr-control-completeness-matrix.csv`"
    source_boundary = "only where they do not widen items 1–4"
    c.check(
        normative_handoff in precedence_lower
        and normative_machine in precedence_lower
        and source_boundary in precedence_lower
        and precedence_lower.index(normative_handoff) < precedence_lower.index(normative_machine) < precedence_lower.index(source_boundary),
        "Input precedence makes the Hermes handoff, resolved prompt and machine contracts normative before source material",
    )
    c.check(
        all(
            term in precedence_lower
            for term in [
                "older installer instructions are evidence—not an activation mechanism",
                "can never enable institutional partitions, p3/p4, a connector, executor, external action",
                "real clinical/qi/research work, or broader data admission",
                "any conflict uses the stricter rule",
            ]
        ),
        "Input precedence prevents immutable source prose from widening the personal target or activating absent capabilities",
    )
    c.check("not_operational_build_required" in build_status.casefold() and "424, all initially `not run`" in build_status.casefold(), "Build status truthfully remains Not operational with all 424 runtime records Not Run")
    c.check("160 unique rows" in gap_report and "duplicate `A2` label" in gap_report and "57/57 package validator" in gap_report and "not runtime execution" in gap_report, "Gap report discloses the inherited duplicate A2 and limits of the legacy structural verifier")


def archive_analysis(path: Path) -> tuple[dict[str, zipfile.ZipInfo], list[str], list[str], list[str], set[str], list[str]]:
    infos: dict[str, zipfile.ZipInfo] = {}
    errors: list[str] = []
    duplicates: list[str] = []
    collisions: list[str] = []
    roots: set[str] = set()
    symlinks: list[str] = []
    folded: dict[str, str] = {}
    file_names: set[str] = set()
    try:
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                name = info.filename
                if not safe_name(name):
                    errors.append(name)
                    continue
                candidate = name[:-1] if name.endswith("/") else name
                roots.add(candidate.split("/", 1)[0])
                if name in infos:
                    duplicates.append(name)
                infos[name] = info
                key = unicodedata.normalize("NFC", candidate).casefold()
                if key in folded and folded[key] != candidate:
                    collisions.append(f"{folded[key]} <> {candidate}")
                folded[key] = candidate
                mode = (info.external_attr >> 16) & 0xFFFF
                if mode and stat.S_ISLNK(mode):
                    symlinks.append(name)
                if mode and not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                    errors.append(f"special:{name}")
                if not info.is_dir():
                    file_names.add(candidate)
            for name in file_names:
                parts = name.split("/")
                for index in range(1, len(parts)):
                    ancestor = "/".join(parts[:index])
                    if ancestor in file_names:
                        errors.append(f"file-directory-prefix:{ancestor}->{name}")
            bad_crc = archive.testzip()
            if bad_crc:
                errors.append(f"crc:{bad_crc}")
    except Exception as error:
        errors.append(str(error))
    return infos, errors, duplicates, collisions, roots, symlinks


def check_archive(c: Checks, path: Path, label: str, expected_root: str | None = None) -> None:
    c.check(path.is_file(), f"{label} exists")
    if not path.is_file():
        return
    infos, errors, duplicates, collisions, roots, symlinks = archive_analysis(path)
    c.check(not errors, f"{label} paths, types, prefix structure and CRC are safe", errors[:10])
    c.check(not duplicates, f"{label} has no duplicate names", duplicates[:10])
    c.check(not collisions, f"{label} has no case or Unicode collisions", collisions[:10])
    c.check(not symlinks, f"{label} contains no symlinks", symlinks[:10])
    c.check(len(roots) == 1, f"{label} has one root", sorted(roots))
    if expected_root is not None:
        c.check(roots == {expected_root}, f"{label} root is exact", sorted(roots))


def compare_archive_tree(c: Checks, archive_path: Path, directory: Path, archive_root: str, label: str) -> None:
    disk = tree_hashes(directory)
    archived: dict[str, str] = {}
    try:
        with zipfile.ZipFile(archive_path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                prefix = archive_root + "/"
                if not info.filename.startswith(prefix):
                    continue
                relative = info.filename[len(prefix):]
                archived[relative] = hashlib.sha256(archive.read(info)).hexdigest()
    except Exception as error:
        c.check(False, f"{label} bytes can be compared", error)
        return
    c.check(set(archived) == set(disk), f"{label} inventory matches", {"archive_only": sorted(set(archived) - set(disk))[:5], "disk_only": sorted(set(disk) - set(archived))[:5]})
    c.check(archived == disk, f"{label} bytes match")


SOURCE_FILES = {
    "source/original-functional-build-master-prompt.md": PROMPT_SHA,
    "source/archives/DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0.zip": BASELINE_ZIP_SHA,
    "source/archives/Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Package-v1.0.zip": LEGACY_COMPLETE_ZIP_SHA,
    "source/complete-reference/Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Hermes-Program.md": COMPLETE_PROGRAM_SHA,
    "source/complete-reference/Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Setup-Guide.md": COMPLETE_SETUP_MD_SHA,
    "source/complete-reference/Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Setup-Guide.docx": COMPLETE_SETUP_DOCX_SHA,
}


def check_sources(c: Checks, package: Path) -> None:
    observed = {name: sha256(package / name) for name in SOURCE_FILES if (package / name).is_file()}
    c.check(observed == SOURCE_FILES, "Every pinned source file hash is exact", {key: observed.get(key) for key in SOURCE_FILES if observed.get(key) != SOURCE_FILES[key]})
    rounds = tree_hashes(package / "source/rounds-domain-pack")
    c.check(rounds == ROUNDS_TREE_HASHES, "ROUNDS source tree has exact seventeen files and hashes")
    c.check(tree_digest(rounds) == ROUNDS_TREE_DIGEST, "ROUNDS deterministic source-tree digest is exact", tree_digest(rounds))
    complete = tree_hashes(package / "source/legacy-reference")
    c.check(complete == COMPLETE_TREE_HASHES, "Complete Edition source tree has exact twenty-two files and hashes")
    c.check(tree_digest(complete) == COMPLETE_TREE_DIGEST, "Complete Edition deterministic source-tree digest is exact", tree_digest(complete))
    c.check(sha256(package / "source/baseline-application/RELEASE-MANIFEST.json") == BASELINE_MANIFEST_SHA, "Baseline manifest hash is exact")
    c.check(sha256(package / "source/baseline-application/SHA256SUMS.txt") == BASELINE_CHECKSUMS_SHA, "Baseline checksum hash is exact")
    check_archive(c, package / "source/archives/DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0.zip", "Baseline source archive", "DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0")
    check_archive(c, package / "source/archives/Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Package-v1.0.zip", "Complete ROUNDS source archive", "Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Package-v1.0")
    compare_archive_tree(c, package / "source/archives/DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0.zip", package / "source/baseline-application", "DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0", "Baseline source archive")
    compare_archive_tree(c, package / "source/archives/Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Package-v1.0.zip", package / "source/legacy-reference", "Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Package-v1.0", "Complete ROUNDS source archive")
    prefix = "Medical-Resident-ROUNDS-SuperPowers-Pack-v1.0/"
    c.check({f"{prefix}{name}": digest for name, digest in rounds.items()} == {name: digest for name, digest in complete.items() if name.startswith(prefix)}, "Standalone ROUNDS tree is byte-identical to the embedded Complete Edition subtree")
    c.check(rounds.get("foundation/Medical-Resident-Life-Training-and-Practice-Foundation.md") == "ee80baf4178aaa6300f20dec013356c314bafd67ac71d8c8e1ab8b4df2d5d021", "Canonical foundation hash is exact and available through the deduplicated source tree")
    assurance_text = (package / "source/rounds-domain-pack/tests/ROUNDS-Release-Assurance.md").read_text(encoding="utf-8")
    # Foundation/overlay rows bold only the ID, while the immutable INT rows
    # bold "INT## CRITICAL" as one label. Capture the canonical ID from both
    # source-authored forms without rewriting the hash-pinned source.
    source_ids = re.findall(
        r"^- \[ \] \*\*((?:[A-R][1-8]|INT(?:0[1-9]|1[0-6])))(?: CRITICAL)?\*\*",
        assurance_text,
        flags=re.MULTILINE,
    )
    c.check(source_ids == expected_canonical_ids(), "Canonical release-assurance source itself has exact A1..R8 plus INT01..16 inventory", source_ids[:10] if source_ids != expected_canonical_ids() else None)


def check_source_inventory(c: Checks, package: Path) -> None:
    inventory = load_json(c, package / "SOURCE-INVENTORY.json", "Source inventory parses")
    if not isinstance(inventory, dict):
        return
    c.check(inventory.get("schema") == "NAIO-MR-ROUNDS-BUILD-KIT-SOURCE-INVENTORY-1", "Source inventory schema is exact")
    hashes = {item.get("id"): item.get("sha256") for item in inventory.get("inputs", [])}
    expected = {
        "functional-build-master-prompt": PROMPT_SHA, "mission-control-v2-baseline": BASELINE_ZIP_SHA,
        "medical-resident-complete-program": COMPLETE_PROGRAM_SHA,
        "medical-resident-complete-setup-md": COMPLETE_SETUP_MD_SHA,
        "medical-resident-complete-setup-docx": COMPLETE_SETUP_DOCX_SHA,
        "medical-resident-complete-legacy-zip": LEGACY_COMPLETE_ZIP_SHA,
    }
    c.check(hashes == expected, "Source inventory records every pinned top-level hash", hashes)
    expected_paths = {
        "functional-build-master-prompt": "source/original-functional-build-master-prompt.md",
        "mission-control-v2-baseline": "source/archives/DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0.zip",
        "medical-resident-complete-program": "source/complete-reference/Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Hermes-Program.md",
        "medical-resident-complete-setup-md": "source/complete-reference/Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Setup-Guide.md",
        "medical-resident-complete-setup-docx": "source/complete-reference/Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Setup-Guide.docx",
        "medical-resident-complete-legacy-zip": "source/archives/Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Package-v1.0.zip",
    }
    c.check({item.get("id"): item.get("path") for item in inventory.get("inputs", [])} == expected_paths, "Source inventory records exact self-contained source paths")
    tree = inventory.get("rounds_source_tree", {})
    c.check(tree.get("deterministic_tree_digest") == ROUNDS_TREE_DIGEST and {item.get("path"): item.get("sha256") for item in tree.get("files", [])} == ROUNDS_TREE_HASHES, "Source inventory records exact ROUNDS tree")
    personalization = inventory.get("personalization", {})
    c.check(personalization == {"raw_soul_or_quiz_answers_bundled": False, "real_discover_packet_bundled": False, "real_soul_quiz_result_bundled": False, "synthetic_examples_are_badge_evidence": False, "synthetic_examples_are_personal_facts": False}, "Source inventory truthfully labels synthetic personalization")
    deduplication = inventory.get("source_deduplication", {})
    c.check(
        deduplication.get("redundant_aliases_omitted") == ["ROUNDS-Medical-Resident-Pack.zip", "Medical-Resident-Life-Training-and-Practice-Hermes-Program.md"]
        and deduplication.get("preserved_equivalents") == [
            "source/archives/Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Package-v1.0.zip",
            "source/rounds-domain-pack/foundation/Medical-Resident-Life-Training-and-Practice-Foundation.md",
        ]
        and "byte-identical" in deduplication.get("reason", ""),
        "Source inventory truthfully records both byte-identical omitted aliases and preserved equivalents",
    )
    deployment = inventory.get("clinical_or_institutional_deployment", {})
    c.check(deployment == {"patient_data_authorized": False, "professional_authority_granted": False, "provisioned_by_this_kit": False, "real_patient_or_institutional_data_bundled": False, "resident_authority_or_supervision_verified": False}, "Source inventory truthfully rejects clinical, resident-authority and institutional claims")


def check_checksums_manifest(c: Checks, package: Path, digests: dict[str, Any], capabilities: Any, sources: Any) -> None:
    checksum_path = package / "SHA256SUMS.txt"
    values, errors = parse_checksums(checksum_path)
    expected_names = set(files(package)) - {"SHA256SUMS.txt"}
    c.check(not errors, "Checksum syntax and paths are safe", errors)
    c.check(set(values) == expected_names, "Checksum inventory is exact", {"missing": sorted(expected_names - set(values))[:10], "extra": sorted(set(values) - expected_names)[:10]})
    c.check(all(sha256(package / name) == digest for name, digest in values.items()), "Every package checksum matches")
    manifest = load_json(c, package / "RELEASE-MANIFEST.json", "Release manifest parses")
    if not isinstance(manifest, dict):
        return
    c.check(manifest.get("schema") == "NAIO-MR-ROUNDS-HERMES-BUILD-KIT-1", "Release manifest schema is exact")
    c.check(manifest.get("build_kit", {}).get("id") == BUILD_ID and manifest.get("build_kit", {}).get("version") == "1.0.0", "Manifest build identity is exact")
    target = manifest.get("target", {})
    c.check(target == {"foundation_namespace": FOUNDATION_NAMESPACE, "home": HOME, "lane": LANE, "namespace": NAMESPACE, "product": PRODUCT, "product_id": PRODUCT_ID, "readiness": "not_operational_build_required", "route": ROUTE, "version": "2.0.0"}, "Manifest target identity and readiness are exact", target)
    expected_counts = {
        "role_lane": 1, "role_adapters": 5, "task_hats": 11, "declared_partitions": 9,
        "personal_available_partitions": 3, "institutional_declared_unavailable_partitions": 6,
        "declared_deployment_contexts": 2, "active_deployment_contexts": 1,
        "protected_record_scopes": 5, "declared_record_types": 17, "machine_record_contracts": 17,
        "core_launchers": 4, "superpowers": 24, "workflows": 24, "templates": 30, "agents": 10,
        "mastery_levels": 4, "capability_domains": 17, "capability_criteria_including_capstone": 77,
        "control_matrix_rows": 216, "cross_cutting_full_stack_scenarios": 48,
        "canonical_assurance_checks": 160, "total_required_execution_records": 424,
    }
    c.check(manifest.get("counts") == expected_counts, "Manifest counts are exact", manifest.get("counts"))
    governance_registry = strict_json_loads((package / "config/MR-Governance-Policy.v1.json").read_text(encoding="utf-8"))
    professional_registry = strict_json_loads((package / "config/MR-Professional-Schema-Registry.v1.json").read_text(encoding="utf-8"))
    partition_contract = governance_registry.get("partitions", {}) if isinstance(governance_registry, dict) else {}
    record_entries = professional_registry.get("entries", []) if isinstance(professional_registry, dict) else []
    required_record_fields = set(professional_registry.get("entry_contract_required_fields", [])) if isinstance(professional_registry, dict) else set()
    machine_contract_count = sum(
        1 for item in record_entries
        if isinstance(item, dict)
        and item.get("machine_contract_status") == "implementation_generated_restrictive_contract"
        and required_record_fields <= set(item)
    )
    c.check(
        manifest.get("counts", {}).get("declared_partitions") == len(PARTITIONS)
        == len(partition_contract.get("personal_available", [])) + len(partition_contract.get("institutional_declared_unavailable", []))
        and manifest.get("counts", {}).get("personal_available_partitions") == len(partition_contract.get("personal_available", [])) == len(PRIVATE_PARTITIONS)
        and manifest.get("counts", {}).get("institutional_declared_unavailable_partitions") == len(partition_contract.get("institutional_declared_unavailable", [])) == len(INSTITUTIONAL_PARTITIONS),
        "Manifest declared, personal-available and institutional-unavailable partition keys align with governance",
    )
    c.check(
        manifest.get("counts", {}).get("declared_record_types") == professional_registry.get("count") == len(record_entries) == len(RECORD_SCHEMAS)
        and [item.get("declared_record_type") for item in record_entries] == RECORD_SCHEMAS
        and manifest.get("counts", {}).get("machine_record_contracts") == machine_contract_count == len(RECORD_SCHEMAS),
        "Manifest declared_record_types and machine_record_contracts keys align one-to-one with the seventeen registry contracts",
    )
    expected_sources = {
        "functional-build-master-prompt": PROMPT_SHA,
        "mission-control-v2-baseline": BASELINE_ZIP_SHA,
        "medical-resident-complete-program": COMPLETE_PROGRAM_SHA,
        "medical-resident-complete-setup-md": COMPLETE_SETUP_MD_SHA,
        "medical-resident-complete-setup-docx": COMPLETE_SETUP_DOCX_SHA,
        "medical-resident-complete-legacy-zip": LEGACY_COMPLETE_ZIP_SHA,
    }
    c.check(manifest.get("sources") == expected_sources, "Manifest pins all six top-level canonical source hashes", manifest.get("sources"))
    defaults = manifest.get("defaults", {})
    c.check(defaults == {"agents": "PERM-P0 Disabled", "external_actions": "Off", "memory": "session_only", "optional_fifth_launcher": "Empty", "perm_p5": "Prohibited", "personal_perm_p4": "Unavailable", "powers": "Available Inactive", "workflows": "Preview Only"}, "Manifest safe defaults are exact", defaults)
    expected_digests = {
        "control_ids": digests["control_id_digest"], "control_matrix_semantics": digests["matrix_semantic_digest"],
        "integration_scenarios": digests["integration_semantic_digest"],
        "capability_configuration": normalized_digest(capabilities), "source_recommendation_registry": normalized_digest(sources),
    }
    c.check(manifest.get("contract_digests") == expected_digests, "Manifest contract digests match staged contracts", manifest.get("contract_digests"))
    entries = manifest.get("files_excluding_manifest_and_checksums", [])
    expected_payload = set(files(package)) - {"RELEASE-MANIFEST.json", "SHA256SUMS.txt"}
    listed = {item.get("path") for item in entries if isinstance(item, dict)}
    c.check(listed == expected_payload and len(entries) == len(expected_payload), "Manifest file inventory is exact")
    c.check(all((package / item["path"]).stat().st_size == item.get("bytes") and sha256(package / item["path"]) == item.get("sha256") for item in entries if isinstance(item, dict) and item.get("path") in expected_payload), "Manifest byte counts and hashes match")
    notice = manifest.get("implementation_notice", "").casefold()
    c.check(all(term in notice for term in ["does not provision", "patient", "clinical", "supervision", "credential", "evaluation", "professional", "external action"]), "Manifest implementation notice rejects borrowed clinical, evaluation and professional authority")


def check_package_filesystem(c: Checks, package: Path) -> None:
    symlinks: list[str] = []
    specials: list[str] = []
    unsafe_modes: list[str] = []
    for path in package.rglob("*"):
        relative = path.relative_to(package).as_posix()
        if path.is_symlink():
            symlinks.append(relative)
            continue
        mode = path.stat().st_mode
        if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            specials.append(relative)
        permissions = stat.S_IMODE(mode)
        expected = {0o755} if path.is_dir() else ({0o644, 0o755} if relative == "tools/verify-build-kit.py" else {0o644})
        if permissions not in expected:
            unsafe_modes.append(f"{relative}:{oct(permissions)} expected one of {sorted(oct(item) for item in expected)}")
    c.check(not symlinks, "Package contains no symlinks", symlinks)
    c.check(not specials, "Package contains no special files", specials)
    if os.name == "nt":
        c.warn(
            "Package mode normalization is not enforceable on Windows",
            "Outer-ZIP mode metadata is still checked when --zip is supplied",
        )
        return
    c.check(not unsafe_modes, "Package modes are normalized and safe", unsafe_modes[:10])


def check_outer_zip(c: Checks, package: Path, zip_path: Path, require_companions: bool) -> None:
    check_archive(c, zip_path, "Final downloadable ZIP", PACKAGE_NAME)
    if not zip_path.is_file():
        return
    compare_archive_tree(c, zip_path, package, PACKAGE_NAME, "Final downloadable ZIP")
    bad_modes: list[str] = []
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            relative = info.filename.split("/", 1)[1]
            permissions = ((info.external_attr >> 16) & 0o7777)
            expected = 0o755 if relative == "tools/verify-build-kit.py" else 0o644
            if permissions != expected:
                bad_modes.append(f"{relative}:{oct(permissions)}")
    c.check(not bad_modes, "Final ZIP preserves normalized safe file modes", bad_modes[:10])
    if require_companions:
        alias = zip_path.parent / ZIP_ALIAS_NAME
        sidecar = zip_path.with_suffix(zip_path.suffix + ".sha256")
        c.check(alias.is_file(), "Unversioned download alias exists")
        c.check(alias.is_file() and sha256(alias) == sha256(zip_path), "Unversioned alias is byte-identical to versioned ZIP")
        c.check(sidecar.is_file(), "Outer ZIP checksum sidecar exists")
        expected = f"{sha256(zip_path)}  {zip_path.name}\n"
        c.check(sidecar.is_file() and sidecar.read_text(encoding="utf-8") == expected, "Outer ZIP checksum sidecar is exact")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--zip", dest="zip_path", type=Path)
    parser.add_argument("--pre-assembly", action="store_true")
    parser.add_argument("--require-release-companions", action="store_true")
    args = parser.parse_args()
    c = Checks()
    package = args.package.resolve()
    c.check(package.is_dir(), "Package directory exists")
    if not package.is_dir():
        return 1
    if not args.pre_assembly:
        c.check(package.name == PACKAGE_NAME, "Versioned package directory name is exact", package.name)
    check_required(c, package, args.pre_assembly)
    check_controlled_text(c, package, args.pre_assembly)
    check_all_json(c, package)
    catalog, agents, capabilities, sources, governance = check_catalogs(c, package)
    check_schemas(c, package)
    digests = check_test_inventories(c, package)
    check_core_docs(c, package)
    if not args.pre_assembly:
        resolved = package / "implementation/MR-Functional-Build-Master-Prompt.md"
        text = resolved.read_text(encoding="utf-8")
        c.check(not any(item in text for item in PLACEHOLDERS), "Resolved master prompt has no unresolved placeholders")
        c.check(all(item in text for item in [BUILD_ID, PRODUCT_ID, LANE, ROUTE, HOME, FOUNDATION_NAMESPACE, NAMESPACE, "not_operational_build_required", "MR-DATA-0/1/2/W/M/P/A/R/C/E/S/X"]), "Resolved master prompt contains exact ROUNDS target metadata and data model")
        inherited_soul_clauses = ["Automatic, safe use of the active Hermes profile and its `SOUL.md`", "Hermes should load that file as its identity", "sending the raw Soul or a derived identity profile", "Hermes uses the profile’s Soul without exposing or duplicating it"]
        c.check(not any(item in text for item in inherited_soul_clauses) and "must never read raw `SOUL.md`" in text and "Never send raw `SOUL.md`" in text, "Resolved master prompt consistently prohibits raw SOUL.md access and transmission")
        inherited_population_clauses = ["Possible role lanes may include, but are not limited to:", "Pre-licensure nursing student or nursing assistant", "A user may activate several complementary roles at the same time"]
        c.check(not any(item in text for item in inherited_population_clauses) and "exactly one isolated population lane: `medical_resident`" in text and "Do not create nursing, attending-physician, administrator, educator, wellness, research-leader, entrepreneur or other population lanes" in text and "exactly one primary task hat" in text and "no more than one secondary hat" in text, "Resolved master prompt enforces the standalone Medical Resident lane and one-primary/optional-secondary hat model")
        sensitive_message_audit = re.search(r"(?:audit|record)[^\n]{0,100}sensitive[- ]message(?: bodies| body)?", text, flags=re.IGNORECASE)
        c.check(
            "Role workspaces" not in text
            and "Record safety events without storing sensitive message bodies" not in text
            and "Audit events without sensitive message bodies" not in text
            and sensitive_message_audit is None,
            "Resolved master prompt contains neither the literal Role workspaces label nor inherited sensitive-message-audit wording",
            sensitive_message_audit.group(0) if sensitive_message_audit else None,
        )
        guide = (package / "implementation/MR-Guide-Page-Content.md").read_text(encoding="utf-8")
        guide_p4 = guide.casefold()
        c.check("p4 does not exist" not in guide_p4 and all(item in guide_p4 for item in ["p3/p4 require a different separately provisioned institutional system", "cannot be enabled here", "p5 is prohibited", "personal one-run ceiling is p2"]), "Guide states the exact personal P2 ceiling, unavailable P3/P4 and prohibited P5 contract")
        readme = (package / "README.md").read_text(encoding="utf-8")
        changelog = (package / "CHANGELOG.md").read_text(encoding="utf-8")
        final_report = (package / "implementation/HERMES-FINAL-HANDOFF-REPORT-TEMPLATE.md").read_text(encoding="utf-8")
        c.check("146 canonical" not in readme + changelog and "216 implementation controls, 48 full-stack scenarios, and all 160 canonical ROUNDS checks—424 runtime records" in readme and "Added 216 controls, 48 resident-specific full-stack scenarios, and 160 canonical checks" in changelog, "README and changelog state 216 + 48 + 160 = 424 test accounting")
        c.check(all(item in final_report for item in ["216 build controls", "48 cross-cutting full-stack scenarios", "144 canonical ROUNDS foundation and overlay checks", "16 canonical Complete Edition integration checks", "Total 424"]) and all(item not in final_report for item in ["63 foundation checks", "82 ROUNDS checks", "1 Complete Edition integration check"]), "Final handoff template states exact 216 + 48 + 144 + 16 = 424 accounting")
        c.check((package / "personalization/input-schemas/discover-packet-input.schema.json").read_bytes() == (package / "schemas/ROUNDS-Discover-Packet.schema.json").read_bytes() and (package / "personalization/input-schemas/soul-profile-input.schema.json").read_bytes() == (package / "schemas/ROUNDS-Soul-Profile.schema.json").read_bytes(), "First-run input schemas are exact ROUNDS adapter copies")
        check_sources(c, package)
        check_source_inventory(c, package)
        check_checksums_manifest(c, package, digests, capabilities, sources)
        check_package_filesystem(c, package)
        if args.zip_path:
            check_outer_zip(c, package, args.zip_path.resolve(), args.require_release_companions)
        elif args.require_release_companions:
            c.check(False, "Release companions require --zip")
    print("\nValidation summary")
    print(f"PASS={len(c.passed)} FAIL={len(c.failed)} WARN={len(c.warnings)}")
    if c.failed:
        print("FAILED ROUNDS MEDICAL RESIDENT BUILD KIT")
        return 1
    print("VERIFIED ROUNDS MEDICAL RESIDENT BUILD KIT — the target application remains not operational until Hermes builds it and executes all 424 required records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
