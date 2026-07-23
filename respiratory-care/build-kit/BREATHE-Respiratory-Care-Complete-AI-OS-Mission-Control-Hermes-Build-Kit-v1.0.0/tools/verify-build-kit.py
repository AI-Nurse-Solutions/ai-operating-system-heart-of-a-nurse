#!/usr/bin/env python3
"""Verify the Respiratory Care Complete AI OS with BREATHE Hermes build kit.

Passing this verifier establishes build-kit integrity only. It never establishes
that the target application, Hermes integration, professional authority, or a
clinical/institutional deployment is operational.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import stat
import sys
import unicodedata
import uuid
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any


PACKAGE_NAME = "BREATHE-Respiratory-Care-Complete-AI-OS-Mission-Control-Hermes-Build-Kit-v1.0.0"
ZIP_ALIAS_NAME = "BREATHE-Respiratory-Care-Complete-AI-OS-Mission-Control-Hermes-Build-Kit.zip"
BUILD_ID = "NAIO-RC-BREATHE-FUNCTIONAL-BUILD-KIT-1.0.0"
PRODUCT = "BREATHE — Respiratory Care Complete AI OS Mission Control"
PRODUCT_ID = "respiratory-care-breathe-mission-control"
LANE = "respiratory_care"
ROUTE = "/respiratory-care"
FOUNDATION_NAMESPACE = "resp_breathe.*"
NAMESPACE = "resp_breathe.*"
HOME = "My BREATHE"
ARCHIVE_MAX_MEMBERS = 4096
ARCHIVE_MAX_MEMBER_BYTES = 128 * 1024 * 1024
ARCHIVE_MAX_EXPANDED_BYTES = 512 * 1024 * 1024
ARCHIVE_MAX_COMPRESSION_RATIO = 200
ARCHIVE_ALLOWED_COMPRESSION = {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}

PROMPT_SHA = "ce884cfc6345cc93a6baec0852cf44feb44d859234ef1dc2b5ac2138df18ebe2"
BASELINE_ZIP_SHA = "69a4dd86659b41136ce9ceb2ceb52512ab567637ab0be29fdc6f6ab6573223c1"
BASELINE_MANIFEST_SHA = "22fed55fd789c933f4e7eb50266f88f8dda47f9fba91ebbe9c2cbe4f0ab99702"
BASELINE_CHECKSUMS_SHA = "e178993d6185b126cc915f0d3026ddb3b07e7c5c7dd432aaf581152db8a5a40e"
COMPLETE_PROGRAM_SHA = "63821c41bd20b34edd7245d2eb640d695b7a80b33e0586893a8387e444d813bb"
COMPLETE_SETUP_MD_SHA = "1ff712f65a167c812b66e32cfa4d588be247617506640772da349592c2e988ff"
COMPLETE_SETUP_DOCX_SHA = "d2bf6752d59cffb0ca772a0387326a7fb918dc846bc14a080b86fc7ea90ae8dc"
LEGACY_COMPLETE_ZIP_SHA = "7fc1d4b0a8dec362bcd41e5e049b1498d70fc2cbfd9d0348f5d7b240172f2edb"
BREATHE_TREE_DIGEST = "9b72b637a333394fef563d3804fb6ce96b974a028ee6670adf03bd67cb52c3c7"
COMPLETE_TREE_DIGEST = "786f169588db9d147984e30d93a433a46d2eb7c3288c19de9988e6f65f2d30dd"

BREATHE_TREE_HASHES = {
    "README.md": "cef7aaac31e22bb68f969f13d283d28cea9815e843fb9c986e43da1282667a7d",
    "breathe/01-B-Begin-Safely.md": "50ffebaf7e5a20e2c0cf38a35f4e6c76402cb64589e5735a8265ea521fd1b263",
    "breathe/02-R-Reason-with-Evidence.md": "824bb6b2b6e3dd65b95c8efa8152104db9ad35405b705d05483f63260ca9af9b",
    "breathe/03-E-Equip-for-Reliability.md": "f70a5e0754b54677a64802400d67d084e011699bae192899d2f75ea6ced35c7c",
    "breathe/04-A-Align-Airway-and-Teams.md": "d985c3aedcbee48f3e5948a752e3a6c58a772cb15566c4060bf0f355c50affc6",
    "breathe/05-T-Teach-Improve-and-Advance.md": "ba74ec35f32ec6293a680a12c48d1a7fa3f498ff01bc91408c778d601168e49c",
    "breathe/06-H-Honor-Humans-and-Future.md": "bed6449a78f977a127cb7ffd5e13aac087aa40365eeeb5a74b4af6dbe3b16d8b",
    "breathe/07-E-Engineer-Ethical-Agents.md": "dcfd343b737e638991fedea5d5098a49579b9c61a2c1ab534e4420eb80dde4a9",
    "core/00-Standalone-Respiratory-Care-Lane-and-Human-Standard.md": "37acb1fa00c0b916594e28ea80d3786ffc666d83859954699461ad3bb4a11950",
    "core/01-Respiratory-Professional-Patient-Team-Device-and-Institution-Trust-Shield.md": "4f2dbc27c328e4edcf639ae420feb6e812703a2fd141c509b1ceb412c71eee24",
    "core/02-BREATHE-SCOPE-CIRCLE-ORBIT-Operating-Core.md": "6de2bd6ddc3926ba022fa991e16e8a5e5cc48bbf9da6c9bdd212926758e0e209",
    "foundation/Respiratory-Care-Life-Practice-and-Professional-Foundation.md": "d7b047d2f76dbd29c6bbc616d7919bb7edb3af994662576a4273881e6ad2a57a",
    "manifest.md": "0faedbc17d49d71ee1097bebb8e011569ed98115253f4fc26cd050ef87f6b893",
    "templates/BREATHE-Cards-and-Templates.md": "c51891e757f190cf7bdf07d92633d1373dd798ee5df70fc86a868d5d44befa81",
    "tests/BREATHE-Release-Assurance.md": "5fe51985df8345c859f5d394448b5e87419a63048515002580ba410b046d1c04",
    "workflows/BREATHE-Workflows-Launch-and-Adoption-Plan.md": "4b5bb85caba0bee2aeeb23e0f8a5a7870c3ad5b1f1c0c28fb6e16b0e92b4316f",
    "workflows/My-BREATHE-Respiratory-Care-Command-Center.md": "332f1041e1ff9a84c21686fcdc5f055c4cf35e86b7b2ffd9401057fc3648be1e",
    "workflows/Respiratory-Role-Setting-and-Situation-Recipes.md": "6aecee0f209c555719684aeea49439aff25ffbdec0c7b101ed176c4e438dc9f5",
}

COMPLETE_TREE_HASHES = {
    "README.md": "b10de0f4f3cdb6ffcb33f09a90440b92c3bd3732f905fcbd68907d3e54f4eadf",
    **{f"Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/{name}": digest for name, digest in BREATHE_TREE_HASHES.items()},
    "Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Hermes-Program.md": COMPLETE_PROGRAM_SHA,
    "Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Setup-Guide.docx": COMPLETE_SETUP_DOCX_SHA,
    "Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Setup-Guide.md": COMPLETE_SETUP_MD_SHA,
    "SHA256SUMS.txt": "9a3cfe815619a97907407bfeb3744ab5ea6c8da22eca2ebffddfaf409fa63f20",
}

CORE_FOUR = ["Orient Shift & Capacity", "Learn & Verify", "Coordinate Care & Equipment", "Review, Escalate & Close"]
POWERS = [
    "Shift & Assignment Readiness Navigator",
    "Workload, Staffing Evidence & Escalation Shield",
    "Fatigue, Recovery & Safe-Transport Navigator",
    "Mission, Family, Finances & Future Compass",
    "Evidence, Guideline & Source-Freshness Navigator",
    "Synthetic ABG, Acid–Base & Gas-Exchange Learning Lab",
    "Synthetic Respiratory Assessment & Pattern-Recognition Studio",
    "Orders, Protocols & Scope Boundary Navigator",
    "Ventilator Modes, Waveforms & Alarm Learning Studio",
    "Oxygen, Aerosol, Humidification & Delivery-Device Learning and Comparison Studio",
    "Equipment, Circuit, Interface & Supply Readiness Mapper",
    "Transport, Procedure & Equipment-Failure Rehearsal",
    "Scope-Aware Respiratory Care Orchestration Mapper",
    "Airway, Code, Rapid Response & Escalation Rehearsal",
    "Interdisciplinary Rounds, Consult & Closed-Loop Coordination Studio",
    "Liberation, NIV, Tracheostomy & Transition Reliability Planner",
    "Patient, Family & Caregiver Education Rehearsal",
    "Preceptor, Competency & Simulation Development Studio",
    "Quality, Safety, Infection Prevention & Implementation Lab",
    "Feedback, Conflict, Psychological Safety & Advocacy Navigator",
    "Credential, Specialty, Career, Research & Leadership Growth Map",
    "AI Agent Charter, Tool, Permission & Data Registry",
    "Multi-Agent Workflow, Device-Boundary & Human-Handoff Designer",
    "Agent Output Audit, Incident, Kill, Rollback & Retirement Controller",
]
WORKFLOWS = [
    "Shift Orientation, Capacity, Top Three & Plan B",
    "Workload Reality, Delay Risk & Human Escalation",
    "Break, Recovery, Health-Care Time & Safe Transport",
    "True North, Family, Finances & Ninety-Day Direction",
    "Evidence, Guideline, Policy & Manufacturer Source Brief",
    "Synthetic ABG, Acid–Base & Gas-Exchange Deliberate Practice",
    "Synthetic Respiratory Assessment, Trend & Bias Rehearsal",
    "SCOPE Role, Credential, Order, Protocol & Permission Check",
    "Synthetic Ventilator Mode, Waveform & Alarm Learning",
    "Oxygen, Aerosol, Humidification & Device Education Comparison",
    "Generic Equipment, Circuit, Interface, Supply & Backup Readiness",
    "Synthetic Transport, Procedure & Equipment-Failure Rehearsal",
    "CIRCLE Respiratory Care-Orchestration Map",
    "Synthetic Airway, Code, Rapid Response & Escalation Rehearsal",
    "Rounds, Consult, Recommendation & Closed-Loop Preparation",
    "Synthetic Liberation, NIV, Tracheostomy & Transition Reliability",
    "Patient, Family, Caregiver Education & Teach-Back Rehearsal",
    "Preceptor, Competency, Simulation & Feedback Development",
    "Quality, Safety, Infection Prevention & PDSA Project",
    "Feedback, Conflict, Safety Concern & Advocacy Preparation",
    "Credential, Specialty, Career, Research & Leadership Growth",
    "ORBIT Agent Charter, Tool, Permission & Data Registry",
    "Multi-Agent Device-Boundary & Human-Handoff Design",
    "Agent Output Audit, Incident, Kill, Rollback & Retirement",
]
TEMPLATES = [
    "BREATHE True North & Protected-Life Promise",
    "Professional Identity, Role, Site & Active-Hat Card",
    "Credential, License, Competency & Expiry Radar",
    "SCOPE Authority and Action Gate Receipt",
    "Shift Capacity, Top Three & Plan B Card",
    "Workload Reality, Staffing Evidence & Escalation Brief",
    "Recovery, Health-Care Time & Safe-Transport Plan",
    "Evidence, Guideline, Policy & Manufacturer Source Brief",
    "Synthetic ABG, Acid–Base & Gas-Exchange Learning Sheet",
    "Synthetic Respiratory Assessment, Trend & Bias Reflection",
    "Order, Protocol, Scope & Human-Owner Comparison Card",
    "Synthetic Ventilator Mode, Waveform & Alarm Worksheet",
    "Oxygen, Aerosol, Humidification & Delivery-Device Comparison",
    "Generic Equipment, Circuit, Interface, Supply & Backup Map",
    "Synthetic Transport, Procedure & Equipment-Failure Rehearsal",
    "CIRCLE Respiratory Care-Orchestration Map",
    "Rounds, Consult, Recommendation & Check-Back Brief",
    "Synthetic Airway, Code & Rapid-Response Rehearsal",
    "Synthetic Liberation, NIV, Tracheostomy & Transition Map",
    "Patient, Family, Caregiver Education & Teach-Back Plan",
    "Preceptor, Simulation, Deliberate-Practice & Feedback Plan",
    "Quality, Safety, Infection Prevention & PDSA Charter",
    "Safety Event or M&M Reflection & Official-System Boundary",
    "Feedback, Conflict, Psychological Safety & Advocacy Brief",
    "NBRC, License, CE, Specialty & Renewal Radar",
    "Career, Education, Research, Leadership & Portfolio Map",
    "Whole-Life Capacity, Family, Finance & Minimum-Mode Plan",
    "ORBIT Agent Charter, Permission & Device-Boundary Envelope",
    "Agent Preview, Test, Run, Review, Incident & Retirement Receipt",
    "Seven-Day Launch & Ninety-Day BREATHE Development Plan",
]
WORKSPACES = [
    ("breathe-shift-capacity-recovery", "Shift, Capacity & Recovery"),
    ("breathe-evidence-learning-credentials", "Evidence, Synthetic Learning & Credentials"),
    ("breathe-equipment-technical-reliability", "Equipment & Technical Reliability"),
    ("breathe-care-orchestration-transitions", "CIRCLE Care Orchestration & Transitions"),
    ("breathe-teaching-quality-leadership-agents", "Teaching, Quality, Leadership & Agent Stewardship"),
]
AGENTS = [
    ("AGT-01", "Shift & Capacity Planner", "PERM-P1"),
    ("AGT-02", "Evidence Scout", "PERM-P2"),
    ("AGT-03", "Synthetic ABG Coach", "PERM-P1"),
    ("AGT-04", "Synthetic Ventilator Learning Coach", "PERM-P1"),
    ("AGT-05", "Source & Claim Verifier", "PERM-P2"),
    ("AGT-06", "Equipment Readiness Mapper", "PERM-P3"),
    ("AGT-07", "Care-Orchestration Draft Assistant", "PERM-P3"),
    ("AGT-08", "Quality & Infection-Prevention Mapper", "PERM-P3"),
    ("AGT-09", "Teaching & Simulation Builder", "PERM-P3"),
    ("AGT-10", "Career & Whole-Life Planner", "PERM-P2"),
]
TASK_HATS = [
    "professional_practice_and_learning", "acute_response_transport_and_transition",
    "equipment_support_and_reliability", "preceptor_educator_and_simulation",
    "quality_research_and_innovation", "leadership_operations_and_team_coordination",
    "career_whole_life_and_recovery",
]
PARTITIONS = [
    "personal_private", "professional_private", "synthetic_learning", "institution_education",
    "institution_quality", "institution_research", "institution_operations", "institution_personnel",
    "institution_agent",
]
PRIVATE_PARTITIONS = PARTITIONS[:3]
INSTITUTIONAL_PARTITIONS = PARTITIONS[3:]
ROLE_STATUSES = [
    "licensed_respiratory_therapist_or_rcp", "student_orientee_or_new_graduate",
    "assistant_technician_or_limited_role", "unknown_stale_expired_or_conflicting",
]
RECORD_SCHEMAS = [
    "professional_identity_context", "credential_license_competency", "scope_order_protocol_source",
    "shift_capacity_recovery", "workload_observation_questions", "equipment_readiness_generic",
    "evidence_guideline_ledger", "synthetic_learning_case", "respiratory_care_orchestration",
    "handoff_transition_rehearsal", "quality_safety_project", "infection_prevention_learning",
    "teaching_preceptor_development", "credential_ce_career", "research_scholarship_portfolio",
    "whole_life_private", "agent_charter_trace", "control_audit_receipt",
]
DATA_CLASS_IDS = [
    "RT-DATA-0", "RT-DATA-1", "RT-DATA-2", "RT-DATA-W", "RT-DATA-M", "RT-DATA-P",
    "RT-DATA-A", "RT-DATA-R", "RT-DATA-C", "RT-DATA-D", "RT-DATA-S", "RT-DATA-X",
]

EXPECTED_MATRIX_COLUMNS = (
    "control_id", "screen", "control", "intended_behavior", "implementation_target", "persisted_data",
    "required_permission", "offline_behavior", "error_behavior", "verification_test", "status",
)
EXPECTED_CONTROL_LEDGER_COLUMNS = ("Test ID", "Area", "Priority", "Verification target", "Required evidence", "Result")
EXPECTED_INTEGRATION_LEDGER_COLUMNS = ("Test ID", "Scenario", "Priority", "Expected result", "Required evidence", "Result")

EXPECTED_MATRIX_ROWS = 216
EXPECTED_INTEGRATION_ROWS = 48
EXPECTED_CANONICAL_ROWS = 160
EXPECTED_TOTAL_EXECUTION_RECORDS = 424

# Filled after the staged contracts are frozen. A mismatch means semantic drift.
CONTROL_ID_DIGEST = "22995145abcfb0cdc7b68ca0bec678a3c03b84bda0103a4f2f82da9a630f008e"
MATRIX_SEMANTIC_DIGEST = "03d213e46ab94a5a72aae672d3f66baf7d550638c25502e6c33f147342208c46"
INTEGRATION_SEMANTIC_DIGEST = "634cf38368cc41e6b845a5d6a96a3ec7a062302f22e729a3de223f2d2313e0dd"
CAPABILITY_DIGEST = "7e5151b7d9b24643cedf239e1a368084a3b24a9e1d15af6482fa52f21adcb661"
SOURCE_REGISTRY_DIGEST = "25e181ddaa7bc85f5b206b1061812a6fbf57461f3ba12442e7aa23a285db6c3c"

STAGING_REQUIRED = (
    ".env.example", "BUILD-STATUS.md", "CHANGELOG.md", "GIVE-THIS-PACKAGE-TO-HERMES.md", "INPUT-PRECEDENCE.md",
    "INSTALL.md", "LICENSE-NOTICE.md", "OPERATOR_HANDOFF.md", "PROCESSING_MESSAGE.md", "README-FIRST.md", "README.md",
    "SOURCE-NOTES.md", "START_HERE.md", "VERSION",
    "config/RT-Agent-Registry.v1.json", "config/RT-Capability-Mastery-Criteria.v1.json", "config/RT-Governance-Policy.v1.json",
    "config/RT-Source-Recommendation-Registry.v1.json", "config/RT-BREATHE-Catalog.v1.json",
    "config/RT-Professional-Schema-Registry.v1.json",
    "implementation/GAP_ANALYSIS.md", "implementation/HERMES-FINAL-HANDOFF-REPORT-TEMPLATE.md",
    "implementation/HERMES-HANDOFF-README.md", "implementation/RT-Acceptance-and-Test-Ledger.md",
    "implementation/RT-Agent-Team-and-Routing.md", "implementation/RT-Architecture-and-Data-Model.md",
    "implementation/RT-Baseline-Gap-Report.md", "implementation/RT-Capability-and-Badge-Evidence-Model.md",
    "implementation/RT-Control-Completeness-Matrix.csv", "implementation/RT-Governance-EDENA-and-Data-Boundaries.md",
    "implementation/RT-Guide-Page-Content.md", "implementation/RT-Personalization-Mapping-Crosswalk.md",
    "implementation/RT-Product-Specification.md", "implementation/RT-Security-and-Privacy-Checklist.md",
    "implementation/RT-Starter-Workspace-Crosswalk.md", "implementation/RT-Synthetic-Sample-Mission.md",
    "implementation/RT-Technical-Implementation-Guide.md", "implementation/RT-User-Installation-Guide.md",
    "personalization/BREATHE-Discover-Packet.synthetic.example.json", "personalization/BREATHE-Mission-Profile.synthetic.example.json",
    "personalization/BREATHE-Soul-Profile.synthetic.example.json", "personalization/README.md",
    "schemas/BREATHE-Discover-Packet.schema.json", "schemas/BREATHE-Mission-Profile.schema.json", "schemas/BREATHE-Soul-Profile.schema.json",
)

RELEASE_REQUIRED = STAGING_REQUIRED + (
    "RELEASE-MANIFEST.json", "SHA256SUMS.txt", "SOURCE-INVENTORY.json", "implementation/RT-Functional-Build-Master-Prompt.md",
    "personalization/input-schemas/discover-packet-input.schema.json", "personalization/input-schemas/soul-profile-input.schema.json",
    "source/original-functional-build-master-prompt.md", "source/archives/DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0.zip",
    "source/archives/Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Package-v1.0.zip",
    "source/complete-reference/Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Hermes-Program.md",
    "source/complete-reference/Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Setup-Guide.md",
    "source/complete-reference/Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Setup-Guide.docx",
    "source/baseline-application/RELEASE-MANIFEST.json", "source/baseline-application/SHA256SUMS.txt", "tools/verify-build-kit.py",
    *(f"source/breathe-domain-pack/{name}" for name in BREATHE_TREE_HASHES),
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
            result.append([cell.strip() for cell in stripped[1:-1].split("|")])
    return result


def expected_canonical_ids() -> list[str]:
    values = [f"RA-{letter}{index:02d}" for letter in "ABCDEFGHIJKLMNOPQR" for index in range(1, 9)]
    values.extend(f"RA-INT{index:02d}" for index in range(1, 17))
    return values


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
        "nurse_practitioner", "/nurse-practitioners/dashboard", "np_wings.*", "np_lppef.*",
        "NP-AGT-", "WINGS-PWR-", "My NP Life, Practice & Purpose Command Center",
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
    c.check(not residue, "Generated contracts contain no NP/WINGS identity residue", residue[:10])


def check_all_json(c: Checks, package: Path) -> None:
    invalid: list[str] = []
    for path in sorted(package.rglob("*.json")):
        try:
            strict_json_loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            invalid.append(f"{path.relative_to(package)}: {error}")
    c.check(not invalid, "Every JSON file strictly parses without duplicate keys or non-finite numbers", invalid[:10])


def check_catalogs(c: Checks, package: Path) -> tuple[Any, Any, Any, Any, Any]:
    catalog = load_json(c, package / "config/RT-BREATHE-Catalog.v1.json", "BREATHE catalog parses")
    agents = load_json(c, package / "config/RT-Agent-Registry.v1.json", "Agent registry parses")
    capabilities = load_json(c, package / "config/RT-Capability-Mastery-Criteria.v1.json", "Capability criteria parse")
    sources = load_json(c, package / "config/RT-Source-Recommendation-Registry.v1.json", "Source recommendation registry parses")
    governance = load_json(c, package / "config/RT-Governance-Policy.v1.json", "Governance policy parses")
    professional = load_json(c, package / "config/RT-Professional-Schema-Registry.v1.json", "Professional schema registry parses")
    if isinstance(catalog, dict):
        c.check(catalog.get("schema") == "NAIO-RT-BREATHE-CATALOG-1" and catalog.get("counts") == {"powers": 24, "workflows": 24, "templates": 30}, "Catalog identity and counts are exact")
        c.check(catalog.get("core_four") == CORE_FOUR and catalog.get("optional_fifth_launcher") is None, "Catalog preserves the exact Core Four and empty fifth launcher")
        c.check([item.get("id") for item in catalog.get("powers", [])] == [f"PWR-{i:02d}" for i in range(1, 25)] and [item.get("display_name") for item in catalog.get("powers", [])] == POWERS, "Exactly twenty-four ordered canonical BREATHE powers")
        c.check(all(item.get("installation_state") == "available_inactive" and item.get("agent_permission") == "PERM-P0 Disabled" and item.get("external_actions") == "off" for item in catalog.get("powers", [])), "Every BREATHE power installs inactive, P0 and external-actions off")
        c.check([item.get("id") for item in catalog.get("workflows", [])] == [f"WF-{i:02d}" for i in range(1, 25)] and [item.get("display_name") for item in catalog.get("workflows", [])] == WORKFLOWS, "Exactly twenty-four ordered canonical workflows")
        c.check(all(item.get("installation_state") == "preview_only" and item.get("external_actions") == "off" for item in catalog.get("workflows", [])), "Every workflow installs Preview only")
        c.check([item.get("id") for item in catalog.get("templates", [])] == [f"TPL-{i:02d}" for i in range(1, 31)] and [item.get("display_name") for item in catalog.get("templates", [])] == TEMPLATES, "Exactly thirty ordered canonical templates")
        c.check(catalog.get("power_lifecycle") == ["Available Inactive", "Previewed", "Approved Inactive", "Active Bounded", "Paused", "Removed"], "Power lifecycle is exact")
        c.check(catalog.get("external_action_lifecycle") == ["Off", "Drafted", "Previewed", "Human-Approved-One-Run", "Staged", "Human-Released", "Confirmed-or-Failed", "Closed"], "External-action lifecycle is exact")
    if isinstance(agents, dict):
        entries = agents.get("entries", [])
        c.check(agents.get("schema") == "NAIO-RT-BREATHE-AGENT-REGISTRY-1" and [(item.get("id"), item.get("name"), item.get("source_proposed_maximum")) for item in entries] == AGENTS, "Exactly ten canonical BREATHE agents and source ceilings")
        c.check(all(item.get("installed_permission") == "PERM-P0 Disabled" for item in entries), "All ten agents install PERM-P0 Disabled")
        ladder = agents.get("permission_ladder", {})
        c.check(list(ladder) == ["PERM-P0 Disabled", "PERM-P1 Private Nonsensitive or Synthetic Draft", "PERM-P2 Private Approved Read-Only", "PERM-P3 Institution-Approved Read or Sandbox", "PERM-P4 One-Run Staged Nonclinical Write", "PERM-P5 Prohibited"], "Permission ladder is exact P0 through P5")
        p4 = ladder.get("PERM-P4 One-Run Staged Nonclinical Write", "").casefold()
        p5 = ladder.get("PERM-P5 Prohibited", "").casefold()
        p4_plain = p4.replace("-", " ")
        c.check(agents.get("personal_p4_available") is False and all(term in p4_plain for term in ["institutional", "one exact", "human release", "excluded from every clinical"]) and all(term in p5 for term in ["autonomous clinical", "device", "recursive delegation"]), "P4 is institutional nonclinical one-run staging and P5 is prohibited")
        forbidden = " ".join(" ".join(item.get("may_not", [])) for item in entries).casefold()
        c.check(all(term in forbidden for term in ["patient", "live devices", "prescribe", "bill", "activate itself", "declare role", "recursively delegate"]), "Agent registry carries patient, device, action, authority and recursion prohibitions")
        c.check(agents.get("orbit_framework") == ["Objective & owner", "Role, risk & responsibility", "Boundaries & budget", "Inspect & test", "Transfer or terminate"], "ORBIT framework is exact")
    if isinstance(capabilities, dict):
        c.check(capabilities.get("schema") == "NAIO-RT-BREATHE-CAPABILITY-MASTERY-CRITERIA-1" and capabilities.get("status") == "normative_build_layer_contract", "Capability schema identity and status are exact")
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
        notice = capabilities.get("noncredential_notice", "").casefold()
        c.check(all(term in notice for term in ["licensure", "certification", "clinical competence", "prescribing authority", "authorization to practice"]), "Capability notice rejects professional credential and authority claims")
        c.check(capabilities.get("contextual_human_review_policy", {}).get("applies_to_all_levels") is True, "Contextual named-human review applies at every level")
        c.check(CAPABILITY_DIGEST == "TO_BE_FILLED" or normalized_digest(capabilities) == CAPABILITY_DIGEST, "Capability configuration digest is frozen", normalized_digest(capabilities))
    if isinstance(sources, dict):
        entries = sources.get("entries", [])
        c.check(sources.get("schema") == "NAIO-RT-BREATHE-SOURCE-RECOMMENDATION-REGISTRY-1" and sources.get("count") == 13, "Source registry identity and count are exact")
        c.check([item.get("id") for item in entries] == [f"RT-SRC-{i:02d}" for i in range(1, 14)], "Source registry is exact RT-SRC-01..13")
        c.check(all(str(item.get("url", "")).startswith("https://") and item.get("reviewed_at") == "2026-07-15" and item.get("source_defined") is True for item in entries), "All source recommendations retain canonical HTTPS URLs and review date")
        c.check(sources.get("rules", {}).get("recommendation_grants_authority") is False and sources.get("rules", {}).get("unknown_id_behavior") == "reject", "Source recommendations grant no authority and reject unknown IDs")
        c.check(SOURCE_REGISTRY_DIGEST == "TO_BE_FILLED" or normalized_digest(sources) == SOURCE_REGISTRY_DIGEST, "Source recommendation registry digest is frozen", normalized_digest(sources))
    if isinstance(governance, dict):
        c.check(governance.get("schema") == "NAIO-RT-BREATHE-GOVERNANCE-POLICY-1", "Governance schema identity is exact")
        c.check(set(governance.get("data_classes", {})) == set(DATA_CLASS_IDS) and len(governance.get("data_classes", {})) == len(DATA_CLASS_IDS), "Governance data classes are exact RT-DATA-0/1/2/W/M/P/A/R/C/D/S/X")
        c.check(governance.get("admitted_data_classes") == DATA_CLASS_IDS[:8] and governance.get("prohibited_data_classes") == DATA_CLASS_IDS[8:], "Governance admission and rejection sets are exact")
        edena = governance.get("edena", {})
        c.check(edena.get("independent_fields") == ["edena_tier", "absolute_stop"] and "cannot be waived" in edena.get("absolute_stop", "").casefold(), "EDENA tier and absolute stop are independent and nonwaivable")
        lifecycle = governance.get("execution", {}).get("artifact_lifecycle")
        c.check(lifecycle == ["Exploration", "Simulation", "Recommendation", "Draft Artifact", "Approved Plan", "Authorized Execution", "Completed Action", "Evaluated Outcome"], "Artifact lifecycle is exact")
        absolute = " ".join(governance.get("absolute_stop_categories", [])).casefold()
        c.check(all(term in absolute for term in ["patient", "device", "prescribing", "credential", "illegal"]), "Absolute-stop catalog covers patient, device, prescribing, secret and illegal action")
        execution = governance.get("execution", {})
        c.check(execution.get("personal_p4_available") is False and execution.get("clinical_or_device_executor") is False and all(term in execution.get("authorized_execution", "").casefold() for term in ["external accountable human", "nonclinical", "human release"]), "Governance freezes external human execution, guarded P4 and no clinical/device executor")
    if isinstance(professional, dict):
        c.check(professional.get("schema") == "NAIO-RT-BREATHE-PROFESSIONAL-SCHEMA-REGISTRY-1" and professional.get("namespace") == NAMESPACE and professional.get("count") == 18, "Professional schema registry identity, namespace and count are exact")
        c.check([item.get("id") for item in professional.get("entries", [])] == RECORD_SCHEMAS and all(item.get("installation_state") == "schema_only_not_operational" for item in professional.get("entries", [])), "Professional registry preserves all eighteen canonical schema IDs as non-operational")
        c.check(professional.get("partition_rule", "").startswith("References resolve only inside the same authorized respiratory-care lane and partition") and "disabled institutionally" in professional.get("partition_rule", ""), "Professional registry freezes same-partition references and institutional whole-life rejection")
    return catalog, agents, capabilities, sources, governance


def check_schemas(c: Checks, package: Path) -> None:
    pairs = [
        ("BREATHE-Discover-Packet.schema.json", "BREATHE-Discover-Packet.synthetic.example.json", "NAIO-RT-DISCOVER-PACKET-ADAPTER-1"),
        ("BREATHE-Soul-Profile.schema.json", "BREATHE-Soul-Profile.synthetic.example.json", "NAIO-RT-SOUL-PROFILE-ADAPTER-1"),
        ("BREATHE-Mission-Profile.schema.json", "BREATHE-Mission-Profile.synthetic.example.json", "NAIO-RT-BREATHE-MISSION-PROFILE-1"),
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
    mission_pair = loaded.get("BREATHE-Mission-Profile.schema.json")
    if mission_pair:
        schema, fixture = mission_pair
        c.check(fixture.get("product_id") == PRODUCT_ID and fixture.get("lane") == LANE and fixture.get("foundation_namespace") == FOUNDATION_NAMESPACE and fixture.get("namespace") == NAMESPACE and fixture.get("canonical_route") == ROUTE, "Synthetic Mission Profile target identity and namespace are exact")
        c.check(fixture.get("professional_status") in ROLE_STATUSES and fixture.get("active_partition") in PRIVATE_PARTITIONS, "Synthetic profile has an exact respiratory status and private partition")
        c.check([(item.get("id"), item.get("title")) for item in fixture.get("workspaces", [])] == WORKSPACES and len([item for item in fixture.get("workspaces", []) if item.get("active")]) == 1, "Synthetic Mission Profile instantiates the five exact workspaces with one active")
        rec = fixture.get("recommended_assets", {})
        c.check(
            [item.get("id") for item in rec.get("powers", [])] == [f"PWR-{i:02d}" for i in range(1, 25)]
            and all(item.get("state") == "available_inactive" for item in rec.get("powers", []))
            and [item.get("id") for item in rec.get("workflows", [])] == [f"WF-{i:02d}" for i in range(1, 25)]
            and all(item.get("state") == "preview_only" for item in rec.get("workflows", []))
            and rec.get("templates") == [f"TPL-{i:02d}" for i in range(1, 31)]
            and [item.get("id") for item in rec.get("agents", [])] == [item[0] for item in AGENTS]
            and rec.get("source_recommendations") == [f"RT-SRC-{i:02d}" for i in range(1, 14)],
            "Synthetic recommendations contain exact ordered 24/24/30/10/13 assets",
        )
        c.check(fixture.get("ai_preferences") == {"agent_permission_state": "PERM-P0 Disabled", "agent_state": "disabled", "background_automation": "off", "default_support": "prepare_only", "external_actions": "off", "p4_available": False, "tools": "disabled"}, "Synthetic AI state is P0 with tools, P4 and execution off")
        c.check(fixture.get("data_boundary", {}).get("rejected_before_echo_and_persistence") == DATA_CLASS_IDS[8:] and not set(fixture.get("data_boundary", {}).get("admitted", [])) & set(DATA_CLASS_IDS[8:]), "Synthetic profile rejects exact patient/device/secret/unknown classes")
        wrong_route = json.loads(json.dumps(fixture)); wrong_route["canonical_route"] = "/wrong"
        wrong_order = json.loads(json.dumps(fixture)); wrong_order["workspaces"][0], wrong_order["workspaces"][1] = wrong_order["workspaces"][1], wrong_order["workspaces"][0]
        bad_uuid = json.loads(json.dumps(fixture)); bad_uuid["profile_id"] = "not-a-uuid"
        bad_bind = json.loads(json.dumps(fixture)); bad_bind["deployment_context"] = "institution_approved_respiratory_workspace"; bad_bind["active_partition"] = "institution_quality"; bad_bind["governance_preferences"]["edition"] = "institutional_managed"; bad_bind["whole_life_available"] = False
        bad_p4 = json.loads(json.dumps(fixture)); bad_p4["ai_preferences"]["p4_available"] = True
        no_active = json.loads(json.dumps(fixture)); [item.update({"active": False}) for item in no_active["workspaces"]]
        two_active = json.loads(json.dumps(fixture)); two_active["workspaces"][0]["active"] = True
        mismatched_active = json.loads(json.dumps(fixture)); mismatched_active["active_workspace_id"] = WORKSPACES[0][0]
        absent_hat = json.loads(json.dumps(fixture)); absent_hat["active_task_hat"] = next(item for item in TASK_HATS if item not in fixture["task_hats"])
        private_institutional_edition = json.loads(json.dumps(fixture)); private_institutional_edition["governance_preferences"]["edition"] = "institutional_managed"
        private_institutional_partition = json.loads(json.dumps(fixture)); private_institutional_partition["active_partition"] = "institution_quality"
        institutional_personal_edition = json.loads(json.dumps(fixture)); institutional_personal_edition["deployment_context"] = "institution_approved_respiratory_workspace"; institutional_personal_edition["active_partition"] = "institution_quality"; institutional_personal_edition["whole_life_available"] = False; institutional_personal_edition["institutional_runtime_bind"] = {"status": "externally_verified", "opaque_ref": "synthetic-bind", "verified_at": "2026-07-20T12:00:00Z", "expires_at": "2026-07-21T12:00:00Z"}
        institutional_whole_life = json.loads(json.dumps(institutional_personal_edition)); institutional_whole_life["governance_preferences"]["edition"] = "institutional_managed"; institutional_whole_life["whole_life_available"] = True; institutional_whole_life["data_boundary"]["admitted"].append("RT-DATA-W")
        verified_without_date = json.loads(json.dumps(fixture)); gate = verified_without_date["scope_context"]["setting_service_scope"]; gate.update({"status": "last_verified", "source_ref": "synthetic-source", "decision_owner": "Synthetic verifier", "verified_at": None})
        patient_class = json.loads(json.dumps(fixture)); patient_class["data_boundary"]["admitted"].append("RT-DATA-C")
        device_class = json.loads(json.dumps(fixture)); device_class["data_boundary"]["admitted"].append("RT-DATA-D")
        p5_agent = json.loads(json.dumps(fixture)); p5_agent["recommended_assets"]["agents"][0]["permission"] = "PERM-P5 Prohibited"
        empty_asset_records = []
        for asset_name in ["powers", "workflows", "templates", "agents", "source_recommendations"]:
            candidate = json.loads(json.dumps(fixture)); candidate["recommended_assets"][asset_name] = []
            empty_asset_records.append(candidate)
        c.check(bool(validate_json_schema(wrong_route, schema)), "Mission schema rejects a wrong route")
        c.check(bool(validate_json_schema(wrong_order, schema)), "Mission schema rejects a wrong workspace order")
        c.check(bool(validate_json_schema(bad_uuid, schema)), "Mission schema rejects malformed UUID")
        c.check(bool(validate_json_schema(bad_bind, schema)), "Mission schema rejects institutional mode without a verified runtime bind")
        c.check(bool(validate_json_schema(bad_p4, schema)), "Mission schema rejects P4 in private mode")
        c.check(bool(validate_json_schema(no_active, schema)), "Mission schema rejects zero active workspaces")
        c.check(bool(validate_json_schema(two_active, schema)), "Mission schema rejects multiple active workspaces")
        c.check(bool(validate_json_schema(mismatched_active, schema)), "Mission schema binds active workspace ID to the active workspace")
        c.check(bool(validate_json_schema(absent_hat, schema)), "Mission schema requires the active task hat in the selected task hats")
        c.check(bool(validate_json_schema(private_institutional_edition, schema)), "Mission schema rejects institutional governance in private mode")
        c.check(bool(validate_json_schema(private_institutional_partition, schema)), "Mission schema rejects an institutional partition in private mode")
        c.check(bool(validate_json_schema(institutional_personal_edition, schema)), "Mission schema rejects personal governance in institutional mode")
        c.check(bool(validate_json_schema(institutional_whole_life, schema)), "Mission schema rejects whole-life availability and RT-DATA-W institutionally")
        c.check(bool(validate_json_schema(verified_without_date, schema)), "Mission schema rejects last_verified without an offset verification timestamp")
        c.check(bool(validate_json_schema(patient_class, schema)) and bool(validate_json_schema(device_class, schema)), "Mission schema rejects patient and device data classes")
        c.check(bool(validate_json_schema(p5_agent, schema)), "Mission schema rejects PERM-P5 agent configuration")
        c.check(all(bool(validate_json_schema(candidate, schema)) for candidate in empty_asset_records), "Mission schema rejects incomplete canonical asset and source recommendation arrays")


def check_test_inventories(c: Checks, package: Path) -> dict[str, Any]:
    path = package / "implementation/RT-Control-Completeness-Matrix.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        matrix = list(reader)
        columns = tuple(reader.fieldnames or ())
    c.check(columns == EXPECTED_MATRIX_COLUMNS, "Control matrix has the exact 11-column contract", columns)
    c.check(len(matrix) == EXPECTED_MATRIX_ROWS, "Control matrix has exactly 216 rows", len(matrix))
    ids = [row.get("control_id", "") for row in matrix]
    c.check(len(set(ids)) == EXPECTED_MATRIX_ROWS and all(re.fullmatch(r"[A-Z][A-Z0-9_]{1,15}-[0-9]{3}", item) for item in ids), "Control IDs are unique and well formed")
    c.check([row.get("control") for row in matrix if row.get("control_id", "").startswith("PWR-")] == POWERS, "PWR controls map one-to-one to the twenty-four BREATHE powers")
    c.check([row.get("control") for row in matrix if row.get("control_id", "").startswith("WF-")] == WORKFLOWS, "WF controls map one-to-one to the twenty-four workflows")
    c.check(all(str(row.get(column, "")).strip() for row in matrix for column in EXPECTED_MATRIX_COLUMNS), "Control matrix has no empty required cell")
    c.check({row.get("status") for row in matrix} == {"Not Run"}, "Every control matrix row starts Not Run")
    ledger = markdown_table_rows((package / "implementation/RT-Acceptance-and-Test-Ledger.md").read_text(encoding="utf-8"))
    c.check(ledger.count(list(EXPECTED_CONTROL_LEDGER_COLUMNS)) == 1 and ledger.count(list(EXPECTED_INTEGRATION_LEDGER_COLUMNS)) == 1, "Acceptance ledger has exact control and integration headers")
    ctl = [row for row in ledger if row and row[0].startswith("CTL-")]
    integration = [row for row in ledger if row and re.fullmatch(r"INT-[0-9]{3}", row[0])]
    canonical = [row for row in ledger if row and re.fullmatch(r"RA-(?:[A-R][0-9]{2}|INT[0-9]{2})", row[0])]
    c.check([row[0] for row in ctl] == [f"CTL-{item}" for item in ids] and all(len(row) == 6 and row[-1] == "Not Run" for row in ctl), "CTL ledger order and result states match the matrix")
    c.check([row[0] for row in integration] == [f"INT-{i:03d}" for i in range(1, 49)] and all(len(row) == 6 and row[-1] == "Not Run" for row in integration), "Integration ledger has exact INT-001..048 Not Run rows")
    c.check(len({row[3] for row in integration}) == 48 and len({row[4] for row in integration}) == 48 and all(len(row[3]) >= 80 and len(row[4]) >= 60 for row in integration), "Every integration scenario has a distinct specific expected result and evidence contract")
    c.check([row[0] for row in canonical] == expected_canonical_ids() and all(len(row) == 4 and row[-1] == "Not Run" for row in canonical), "Canonical ledger exactly maps RA-A01..RA-R08 plus RA-INT01..16")
    c.check(len(ctl) + len(integration) == 264 and len(canonical) == 160, "Ledger counts are exactly 264 target and 160 canonical")
    text = (package / "implementation/RT-Acceptance-and-Test-Ledger.md").read_text(encoding="utf-8")
    c.check("Total required execution records: 424" in text, "Ledger states exact 216 + 48 + 160 = 424 accounting")
    values = {
        "control_id_digest": hashlib.sha256(("\n".join(ids) + "\n").encode()).hexdigest(),
        "matrix_semantic_digest": normalized_digest([[row[column] for column in EXPECTED_MATRIX_COLUMNS] for row in matrix]),
        "integration_semantic_digest": normalized_digest(integration),
    }
    c.check(CONTROL_ID_DIGEST == "TO_BE_FILLED" or values["control_id_digest"] == CONTROL_ID_DIGEST, "Control-ID digest is frozen", values["control_id_digest"])
    c.check(MATRIX_SEMANTIC_DIGEST == "TO_BE_FILLED" or values["matrix_semantic_digest"] == MATRIX_SEMANTIC_DIGEST, "Control-matrix semantic digest is frozen", values["matrix_semantic_digest"])
    c.check(INTEGRATION_SEMANTIC_DIGEST == "TO_BE_FILLED" or values["integration_semantic_digest"] == INTEGRATION_SEMANTIC_DIGEST, "Integration-scenario semantic digest is frozen", values["integration_semantic_digest"])
    return values


def check_core_docs(c: Checks, package: Path) -> None:
    paths = [
        package / "GIVE-THIS-PACKAGE-TO-HERMES.md",
        package / "implementation/RT-Product-Specification.md",
        package / "implementation/RT-Governance-EDENA-and-Data-Boundaries.md",
        package / "implementation/RT-Architecture-and-Data-Model.md",
        package / "implementation/RT-Guide-Page-Content.md",
        package / "implementation/RT-Security-and-Privacy-Checklist.md",
        package / "implementation/RT-Agent-Team-and-Routing.md",
        package / "implementation/RT-Technical-Implementation-Guide.md",
        package / "config/RT-Professional-Schema-Registry.v1.json",
        package / "schemas/BREATHE-Mission-Profile.schema.json",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths).casefold()
    normalized_text = text.replace("-", " ")
    c.check(all(term.casefold() in text for term in [BUILD_ID, PRODUCT_ID, LANE, ROUTE, HOME, FOUNDATION_NAMESPACE, NAMESPACE]), "Core contracts document exact build identity")
    c.check(all(term in text for term in ["patient", "real case", "live care", "diagnosis", "treatment", "triage", "prescribing", "dosing", "ordering", "charting", "coding", "billing", "claims"]), "Core contracts document the patient and clinical boundary")
    c.check(all(term in normalized_text for term in ["live device", "alarm", "waveform", "setting", "serial", "device", "control"]), "Core contracts document the full device boundary")
    c.check(all(term in text for term in ["scope", "circle", "orbit", "last_verified", "unverified — official confirmation required"]), "Core contracts document SCOPE/CIRCLE/ORBIT and verification truth")
    c.check(all(term in text for term in ["edena_tier", "absolute_stop", "never waivable", "new clean fictional"]), "Core contracts document independent EDENA and absolute-stop behavior")
    c.check(all(term in text for term in ["authorized execution", "external", "completed action", "verified external", "human release"]), "Core contracts document external human execution truth")
    c.check(all(term in text for term in ["p0", "p1", "p2", "p3", "p4", "nonclinical", "p5", "prohibited"]), "Core contracts document exact P0–P5 boundaries")
    c.check(all(name.casefold() in text for name in RECORD_SCHEMAS), "Core contracts enumerate all eighteen canonical professional-owned schemas")
    c.check(all(item.casefold() in text for item in PARTITIONS) and all(item.casefold() in text for item in TASK_HATS), "Core contracts enumerate exact task hats and isolated partitions")
    c.check(all(item.casefold() in text for item in ["rt-data-c", "rt-data-d", "rt-data-s", "rt-data-x", "whole_life_private"]), "Core contracts document rejected classes and whole-life isolation")
    c.check(all(term in normalized_text for term in ["keyboard", "screen reader", "noncolor", "reduced motion", "plain"]), "Core contracts document accessibility and human-design boundaries")
    c.check(all(term in normalized_text for term in ["backup", "restore", "rollback", "breathe removal", "uninstall"]), "Core contracts document recovery boundaries")
    handoff = (package / "implementation/HERMES-FINAL-HANDOFF-REPORT-TEMPLATE.md").read_text(encoding="utf-8")
    c.check(all(state in handoff for state in ["**Operational**", "**Core operational; AI setup pending**", "**Not operational**"]), "Handoff contains the three exact readiness states")


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
            archive_infos = archive.infolist()
            if len(archive_infos) > ARCHIVE_MAX_MEMBERS:
                errors.append(f"member-limit:{len(archive_infos)}")
            expanded_bytes = 0
            for info in archive_infos:
                name = info.filename
                raw_name = getattr(info, "orig_filename", name)
                if "\x00" in raw_name or raw_name != name:
                    errors.append(f"raw-normalized-mismatch:{raw_name!r}")
                    continue
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
                if info.flag_bits & 1:
                    errors.append(f"encrypted:{name}")
                if info.compress_type not in ARCHIVE_ALLOWED_COMPRESSION:
                    errors.append(f"compression:{name}:{info.compress_type}")
                if info.file_size > ARCHIVE_MAX_MEMBER_BYTES:
                    errors.append(f"member-bytes:{name}:{info.file_size}")
                expanded_bytes += info.file_size
                if expanded_bytes > ARCHIVE_MAX_EXPANDED_BYTES:
                    errors.append(f"expanded-bytes:{expanded_bytes}")
                if info.file_size and info.compress_size == 0:
                    errors.append(f"compression-ratio:{name}:infinite")
                elif info.compress_size and info.file_size / info.compress_size > ARCHIVE_MAX_COMPRESSION_RATIO:
                    errors.append(f"compression-ratio:{name}:{info.file_size / info.compress_size:.2f}")
                mode = (info.external_attr >> 16) & 0o177777
                if stat.S_ISLNK(mode):
                    symlinks.append(name)
                expected_modes = {stat.S_IFREG | 0o644, stat.S_IFREG | 0o755}
                if info.is_dir() or mode not in expected_modes:
                    errors.append(f"mode:{name}:{oct(mode)}")
                else:
                    file_names.add(candidate)
            for name in file_names:
                parts = name.split("/")
                for index in range(1, len(parts)):
                    ancestor = "/".join(parts[:index])
                    if ancestor in file_names:
                        errors.append(f"file-directory-prefix:{ancestor}->{name}")
            # CRC reads payloads and therefore runs only after all metadata gates pass.
            if not errors and not duplicates and not collisions and not symlinks:
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
    _, errors, duplicates, collisions, _, symlinks = archive_analysis(archive_path)
    if errors or duplicates or collisions or symlinks:
        c.check(False, f"{label} bytes can be compared only after metadata validation", {
            "errors": errors[:10], "duplicates": duplicates[:10],
            "collisions": collisions[:10], "symlinks": symlinks[:10],
        })
        return
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
    "source/archives/Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Package-v1.0.zip": LEGACY_COMPLETE_ZIP_SHA,
    "source/complete-reference/Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Hermes-Program.md": COMPLETE_PROGRAM_SHA,
    "source/complete-reference/Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Setup-Guide.md": COMPLETE_SETUP_MD_SHA,
    "source/complete-reference/Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Setup-Guide.docx": COMPLETE_SETUP_DOCX_SHA,
}


def check_sources(c: Checks, package: Path) -> None:
    observed = {name: sha256(package / name) for name in SOURCE_FILES if (package / name).is_file()}
    c.check(observed == SOURCE_FILES, "Every pinned source file hash is exact", {key: observed.get(key) for key in SOURCE_FILES if observed.get(key) != SOURCE_FILES[key]})
    breathe = tree_hashes(package / "source/breathe-domain-pack")
    c.check(breathe == BREATHE_TREE_HASHES, "BREATHE source tree has exact eighteen files and hashes")
    c.check(tree_digest(breathe) == BREATHE_TREE_DIGEST, "BREATHE deterministic source-tree digest is exact", tree_digest(breathe))
    complete = tree_hashes(package / "source/legacy-reference")
    c.check(complete == COMPLETE_TREE_HASHES, "Complete Edition source tree has exact twenty-three files and hashes")
    c.check(tree_digest(complete) == COMPLETE_TREE_DIGEST, "Complete Edition deterministic source-tree digest is exact", tree_digest(complete))
    c.check(sha256(package / "source/baseline-application/RELEASE-MANIFEST.json") == BASELINE_MANIFEST_SHA, "Baseline manifest hash is exact")
    c.check(sha256(package / "source/baseline-application/SHA256SUMS.txt") == BASELINE_CHECKSUMS_SHA, "Baseline checksum hash is exact")
    check_archive(c, package / "source/archives/DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0.zip", "Baseline source archive", "DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0")
    check_archive(c, package / "source/archives/Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Package-v1.0.zip", "Complete BREATHE source archive", "Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Package-v1.0")
    compare_archive_tree(c, package / "source/archives/DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0.zip", package / "source/baseline-application", "DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0", "Baseline source archive")
    compare_archive_tree(c, package / "source/archives/Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Package-v1.0.zip", package / "source/legacy-reference", "Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Package-v1.0", "Complete BREATHE source archive")
    c.check({f"Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/{name}": digest for name, digest in breathe.items()} == {name: digest for name, digest in complete.items() if name.startswith("Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0/")}, "Standalone BREATHE tree is byte-identical to the embedded Complete Edition subtree")


def check_source_inventory(c: Checks, package: Path) -> None:
    inventory = load_json(c, package / "SOURCE-INVENTORY.json", "Source inventory parses")
    if not isinstance(inventory, dict):
        return
    c.check(inventory.get("schema") == "NAIO-RT-BREATHE-BUILD-KIT-SOURCE-INVENTORY-1", "Source inventory schema is exact")
    hashes = {item.get("id"): item.get("sha256") for item in inventory.get("inputs", [])}
    expected = {
        "functional-build-master-prompt": PROMPT_SHA, "mission-control-v2-baseline": BASELINE_ZIP_SHA,
        "respiratory-care-complete-program": COMPLETE_PROGRAM_SHA,
        "respiratory-care-complete-setup-md": COMPLETE_SETUP_MD_SHA,
        "respiratory-care-complete-setup-docx": COMPLETE_SETUP_DOCX_SHA,
        "respiratory-care-complete-legacy-zip": LEGACY_COMPLETE_ZIP_SHA,
    }
    c.check(hashes == expected, "Source inventory records every pinned top-level hash", hashes)
    tree = inventory.get("breathe_source_tree", {})
    c.check(tree.get("deterministic_tree_digest") == BREATHE_TREE_DIGEST and {item.get("path"): item.get("sha256") for item in tree.get("files", [])} == BREATHE_TREE_HASHES, "Source inventory records exact BREATHE tree")
    personalization = inventory.get("personalization", {})
    c.check(personalization == {"raw_soul_or_quiz_answers_bundled": False, "real_discover_packet_bundled": False, "real_soul_quiz_result_bundled": False, "synthetic_examples_are_badge_evidence": False, "synthetic_examples_are_personal_facts": False}, "Source inventory truthfully labels synthetic personalization")
    deployment = inventory.get("clinical_or_institutional_deployment", {})
    c.check(deployment == {"device_connection_or_control_granted": False, "patient_data_authorized": False, "professional_authority_granted": False, "provisioned_by_this_kit": False, "real_patient_device_or_institutional_data_bundled": False}, "Source inventory truthfully rejects clinical, device and institutional authority")


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
    c.check(manifest.get("schema") == "NAIO-RT-BREATHE-HERMES-BUILD-KIT-1", "Release manifest schema is exact")
    c.check(manifest.get("build_kit", {}).get("id") == BUILD_ID and manifest.get("build_kit", {}).get("version") == "1.0.0", "Manifest build identity is exact")
    target = manifest.get("target", {})
    c.check(target == {"foundation_namespace": FOUNDATION_NAMESPACE, "home": HOME, "lane": LANE, "namespace": NAMESPACE, "product": PRODUCT, "product_id": PRODUCT_ID, "readiness": "not_operational_build_required", "route": ROUTE, "version": "2.0.0"}, "Manifest target identity and readiness are exact", target)
    expected_counts = {
        "role_lane": 1, "task_hats": 7, "operational_partitions": 9, "deployment_contexts": 2,
        "protected_workspaces": 5, "record_schemas": 18,
        "core_launchers": 4, "superpowers": 24, "workflows": 24, "templates": 30, "agents": 10,
        "mastery_levels": 4, "capability_domains": 17, "capability_criteria_including_capstone": 77,
        "control_matrix_rows": 216, "cross_cutting_full_stack_scenarios": 48,
        "canonical_assurance_checks": 160, "total_required_execution_records": 424,
    }
    c.check(manifest.get("counts") == expected_counts, "Manifest counts are exact", manifest.get("counts"))
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
    c.check(all(term in notice for term in ["does not provision", "patient", "clinical", "device", "professional authority", "external action"]), "Manifest implementation notice rejects borrowed clinical, device and professional authority")


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
        resolved = package / "implementation/RT-Functional-Build-Master-Prompt.md"
        text = resolved.read_text(encoding="utf-8")
        c.check(not any(item in text for item in PLACEHOLDERS), "Resolved master prompt has no unresolved placeholders")
        c.check(all(item in text for item in [BUILD_ID, PRODUCT_ID, LANE, ROUTE, HOME, FOUNDATION_NAMESPACE, NAMESPACE, "not_operational_build_required", "RT-DATA-0/1/2/W/M/P/A/R/C/D/S/X"]), "Resolved master prompt contains exact BREATHE target metadata and data model")
        inherited_soul_clauses = ["Automatic, safe use of the active Hermes profile and its `SOUL.md`", "Hermes should load that file as its identity", "sending the raw Soul or a derived identity profile", "Hermes uses the profile’s Soul without exposing or duplicating it"]
        c.check(not any(item in text for item in inherited_soul_clauses) and "must never read raw `SOUL.md`" in text and "Never send raw `SOUL.md`" in text, "Resolved master prompt consistently prohibits raw SOUL.md access and transmission")
        inherited_population_clauses = ["Possible role lanes may include, but are not limited to:", "Pre-licensure nursing student or nursing assistant", "A user may activate several complementary roles at the same time"]
        c.check(not any(item in text for item in inherited_population_clauses) and "exactly one isolated population lane: `respiratory_care`" in text and "Do not create nursing, physician, administrator, wellness, research-leader, entrepreneur or other population lanes" in text, "Resolved master prompt enforces the standalone Respiratory Care population lane")
        guide = (package / "implementation/RT-Guide-Page-Content.md").read_text(encoding="utf-8")
        guide_p4 = guide.casefold()
        c.check("p4 does not exist" not in guide_p4 and "p3 is only a deterministic local personal reminder" not in guide_p4 and all(item in guide_p4 for item in ["p3 is available only as institution-approved read or sandbox access", "no write authority", "target ships with no executor", "p4 is unavailable in the personal edition", "separately governed institutional extension", "one exact nonclinical p4 action", "named-human review and release", "p5 is prohibited"]), "Guide states the exact P3, no-executor, guarded P4 and P5 contract")
        readme = (package / "README.md").read_text(encoding="utf-8")
        changelog = (package / "CHANGELOG.md").read_text(encoding="utf-8")
        final_report = (package / "implementation/HERMES-FINAL-HANDOFF-REPORT-TEMPLATE.md").read_text(encoding="utf-8")
        c.check("146 canonical" not in readme + changelog and all("216-control matrix, 48 cross-cutting scenarios and 160 canonical compatibility records" in item for item in [readme, changelog.replace("Added 216 controls", "216-control matrix")]), "README and changelog state 216 + 48 + 160 test accounting")
        c.check(all(item in final_report for item in ["216 build controls", "48 cross-cutting scenarios", "144 canonical BREATHE foundation and overlay checks", "16 canonical Complete Edition integration checks", "Total 424"]) and all(item not in final_report for item in ["63 foundation checks", "82 BREATHE checks", "1 Complete Edition integration check"]), "Final handoff template states exact 216 + 48 + 144 + 16 = 424 accounting")
        c.check((package / "personalization/input-schemas/discover-packet-input.schema.json").read_bytes() == (package / "schemas/BREATHE-Discover-Packet.schema.json").read_bytes() and (package / "personalization/input-schemas/soul-profile-input.schema.json").read_bytes() == (package / "schemas/BREATHE-Soul-Profile.schema.json").read_bytes(), "First-run input schemas are exact BREATHE adapter copies")
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
        print("FAILED BREATHE RESPIRATORY CARE BUILD KIT")
        return 1
    print("VERIFIED BREATHE RESPIRATORY CARE BUILD KIT — the target application remains not operational until Hermes builds it and executes all 424 required records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
