from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import time
import urllib.error
import urllib.request
import zipfile
from collections import Counter
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DELIVERABLES = ROOT / "deliverables"
PACKAGE = DELIVERABLES / "DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0"
ZIP_PATH = DELIVERABLES / "DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0.zip"
ZIP_ALIAS = DELIVERABLES / "DISCOVER-Nurse-AI-OS-Mission-Control.zip"

HTML = PACKAGE / "index.html"
APP_JS = PACKAGE / "assets" / "app.js"
CSS = PACKAGE / "assets" / "styles.css"
SERVER = PACKAGE / "server.mjs"
RELEASE_MANIFEST = PACKAGE / "RELEASE-MANIFEST.json"
CHECKSUMS = PACKAGE / "SHA256SUMS.txt"
DOM_QA = ROOT / "qa" / "discover-mission-control-v2-dom-qa.json"
VISUAL_QA = ROOT / "qa" / "discover-mission-control-v2-visual-qa" / "visual-qa-report.json"

VERSION = "2.0.0"
PRODUCT_ID = "discover-nurse-ai-os-mission-control"
HEALTH_PRODUCT = "DISCOVER-NURSE-AI-OS-MISSION-CONTROL"
HERMES_COMPANION_ID = "NAIOS-MISSION-CONTROL-LOCAL-2.0.0"
EDENA_POLICY = "EDENA-MC-ADVISORY@1.0.0-draft"
STORAGE_KEY = "discover.nurse-ai-os.mission-control.v2"
ROLE_IDS = [
    "shared-identity",
    "research-innovation",
    "prelicensure-support",
    "staff-nurse",
    "advanced-practice",
    "nurse-educator",
    "medical-resident",
    "nurse-manager",
    "clinic-manager",
    "hospital-administrator",
    "wellness-manager",
    "quality-safety",
    "researcher",
    "digital-ai",
    "entrepreneur",
    "community",
    "advanced-studies",
]
CAPABILITY_IDS = [
    "ai-literacy",
    "prompt-design",
    "evidence-research",
    "critical-thinking",
    "structured-problem-solving",
    "workflow-design",
    "project-management",
    "privacy-stewardship",
    "ethical-ai",
    "edena-governance",
    "agent-supervision",
    "multi-agent",
    "knowledge-base",
    "automation-design",
    "artifact-creation",
    "evaluation-qi",
    "role-development",
]
STAGES = ["assess", "define", "plan", "implement", "evaluate"]
ARTIFACT_STATES = [
    "exploration",
    "simulation",
    "recommendation",
    "draft_artifact",
    "approved_plan",
    "authorized_execution",
    "completed_action",
    "evaluated_outcome",
]
EXPECTED_COUNTS = {
    "roles": 17,
    "powers": 24,
    "workflows": 24,
    "templates": 30,
    "mission_stages": 5,
    "artifact_states": 8,
    "capabilities": 17,
    "mastery_levels": 4,
    "guide_sections": 12,
}

PASSED = 0
FAILED = 0


class HtmlAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.references: list[str] = []
        self.remote_resources: list[str] = []
        self.scripts: list[str] = []
        self.inline_scripts = 0
        self.styles: list[str] = []
        self.inline_handlers: list[str] = []
        self.fragment_links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if data.get("id"):
            self.ids.append(data["id"] or "")
        for key in ("for", "aria-labelledby", "aria-describedby", "aria-controls"):
            if data.get(key):
                self.references.extend((data[key] or "").split())
        for key, value in attrs:
            normalized = value or ""
            if key.lower().startswith("on"):
                self.inline_handlers.append(f"{tag}[{key}]")
            if key in {"src", "href", "action", "poster"} and normalized.startswith(("http://", "https://", "//")):
                self.remote_resources.append(normalized)
        href = data.get("href") or ""
        if href.startswith("#") and len(href) > 1:
            self.fragment_links.append(href[1:])
        if tag == "script":
            if data.get("src"):
                self.scripts.append(data["src"] or "")
            else:
                self.inline_scripts += 1
        if tag == "link" and "stylesheet" in (data.get("rel") or "").split() and data.get("href"):
            self.styles.append(data["href"] or "")


def check(condition: bool, message: str, detail: object | None = None) -> None:
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"PASS  {message}")
    else:
        FAILED += 1
        suffix = f" — {detail}" if detail is not None else ""
        print(f"FAIL  {message}{suffix}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def safe_relative_name(name: str) -> bool:
    pure = PurePosixPath(name)
    return bool(
        name
        and "\x00" not in name
        and "\\" not in name
        and not pure.is_absolute()
        and ".." not in pure.parts
        and not (pure.parts and ":" in pure.parts[0])
    )


def read_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        check(False, f"JSON parses: {path.relative_to(ROOT)}", error)
        return None


def is_iso_datetime(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.tzinfo is not None
    except ValueError:
        return False


def json_type_matches(value: object, type_name: str) -> bool:
    return {
        "null": value is None,
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
    }.get(type_name, False)


def resolve_json_pointer(root: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise ValueError(f"only local JSON pointers are supported: {reference}")
    current: Any = root
    for raw in reference[2:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        current = current[token]
    if not isinstance(current, dict):
        raise ValueError(f"JSON pointer does not resolve to an object: {reference}")
    return current


def schema_errors(instance: Any, schema: dict[str, Any], root: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    if "$ref" in schema:
        try:
            target = resolve_json_pointer(root, schema["$ref"])
        except (KeyError, TypeError, ValueError) as error:
            return [f"{path}: invalid $ref {schema.get('$ref')!r}: {error}"]
        return schema_errors(instance, target, root, path)

    if "oneOf" in schema:
        outcomes = [schema_errors(instance, branch, root, path) for branch in schema["oneOf"]]
        valid = sum(not branch_errors for branch_errors in outcomes)
        if valid != 1:
            errors.append(f"{path}: expected exactly one oneOf branch, found {valid}")
        return errors

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {instance!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: value {instance!r} is not in enum")

    declared_type = schema.get("type")
    if declared_type is not None:
        allowed = declared_type if isinstance(declared_type, list) else [declared_type]
        if not any(json_type_matches(instance, item) for item in allowed):
            errors.append(f"{path}: expected type {allowed}, got {type(instance).__name__}")
            return errors

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                errors.append(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extras = sorted(set(instance) - set(properties))
            if extras:
                errors.append(f"{path}: unexpected properties {extras}")
        for key, child_schema in properties.items():
            if key in instance:
                errors.extend(schema_errors(instance[key], child_schema, root, f"{path}.{key}"))

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: has {len(instance)} items, minimum is {schema['minItems']}")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: has {len(instance)} items, maximum is {schema['maxItems']}")
        if schema.get("uniqueItems"):
            canonical = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in instance]
            if len(canonical) != len(set(canonical)):
                errors.append(f"{path}: items are not unique")
        if isinstance(schema.get("items"), dict):
            for index, item in enumerate(instance):
                errors.extend(schema_errors(item, schema["items"], root, f"{path}[{index}]"))
        if isinstance(schema.get("contains"), dict):
            matches = sum(not schema_errors(item, schema["contains"], root, f"{path}[*]") for item in instance)
            minimum = schema.get("minContains", 1)
            maximum = schema.get("maxContains")
            if matches < minimum or (maximum is not None and matches > maximum):
                errors.append(f"{path}: contains matched {matches}; expected {minimum}..{maximum or 'unbounded'}")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: string shorter than {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{path}: string longer than {schema['maxLength']}")
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            errors.append(f"{path}: string does not match {schema['pattern']!r}")
        if schema.get("format") == "date-time" and not is_iso_datetime(instance):
            errors.append(f"{path}: value is not an offset-aware ISO date-time")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: value is below {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: value is above {schema['maximum']}")
    return errors


def verify_server(node: str) -> None:
    process = subprocess.Popen(
        [node, str(SERVER)],
        cwd=PACKAGE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    response: Any | None = None
    try:
        for _ in range(40):
            try:
                response = urllib.request.urlopen("http://127.0.0.1:43127/health", timeout=0.5)
                break
            except Exception:
                if process.poll() is not None:
                    break
                time.sleep(0.1)
        check(response is not None and response.status == 200, "Loopback health endpoint starts on 127.0.0.1:43127")
        if response is None:
            stdout, stderr = process.communicate(timeout=1) if process.poll() is not None else ("", "")
            check(False, "Loopback server emitted no startup error", (stdout + stderr).strip())
            return

        health_headers = response.headers
        try:
            health = json.loads(response.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            health = {"parse_error": str(error)}
        expected_health = {
            "status": "ok",
            "product": HEALTH_PRODUCT,
            "version": VERSION,
            "integration": "manual_handoff",
            "externalActions": False,
        }
        check(health == expected_health, "Health response has the exact product, version and no-execution shape", health)
        check(health_headers.get("Cache-Control") == "no-store", "Health response is not cached", health_headers.get("Cache-Control"))

        index = urllib.request.urlopen("http://127.0.0.1:43127/", timeout=2)
        body = index.read().decode("utf-8")
        csp = index.headers.get("Content-Security-Policy", "")
        required_csp = [
            "default-src 'self' data: blob:",
            "script-src 'self'",
            "style-src 'self'",
            "connect-src 'none'",
            "object-src 'none'",
            "base-uri 'none'",
            "form-action 'none'",
            "frame-ancestors 'none'",
        ]
        check("DISCOVER · Nurse AI OS Mission Control" in body, "Loopback server returns the v2 dashboard")
        check(all(directive in csp for directive in required_csp), "Server Content Security Policy is fail-closed", csp)
        check(index.headers.get("X-Frame-Options") == "DENY", "Loopback response blocks framing")
        check(index.headers.get("X-Content-Type-Options") == "nosniff", "Loopback response disables MIME sniffing")
        check(index.headers.get("Referrer-Policy") == "no-referrer", "Loopback response suppresses referrers")

        head_request = urllib.request.Request("http://127.0.0.1:43127/", method="HEAD")
        head = urllib.request.urlopen(head_request, timeout=2)
        check(head.status == 200 and head.read() == b"", "Loopback server supports read-only HEAD requests")

        post_request = urllib.request.Request("http://127.0.0.1:43127/", data=b"x", method="POST")
        try:
            urllib.request.urlopen(post_request, timeout=2)
            post_status = 200
        except urllib.error.HTTPError as error:
            post_status = error.code
        check(post_status == 405, "Loopback server exposes no write endpoint", post_status)

        try:
            urllib.request.urlopen("http://127.0.0.1:43127/..%2F..%2Fetc%2Fpasswd", timeout=2)
            traversal_status = 200
        except urllib.error.HTTPError as error:
            traversal_status = error.code
        check(traversal_status in {400, 403, 404}, "Loopback server rejects path traversal", traversal_status)
    finally:
        if response is not None:
            response.close()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)


def main() -> None:
    required = [
        "README-FIRST.md",
        "README.md",
        "VERSION",
        "index.html",
        "assets/app.js",
        "assets/styles.css",
        "server.mjs",
        "Start-DISCOVER.command",
        "Start-DISCOVER.bat",
        "start-discover.sh",
        "guide/DISCOVER-Mission-Control-Setup-Guide.md",
        "hermes/DISCOVER-Dashboard-Hermes-Integration-Installer.md",
        "hermes/Hermes-Capability-State.md",
        "config/mission-control-manifest.json",
        "config/role-dashboards.json",
        "config/discover-packet-input.schema.json",
        "config/soul-profile-input.schema.json",
        "config/mission.schema.json",
        "config/capability-evidence.schema.json",
        "config/edena-policy.json",
        "examples/deidentified-discover-packet.json",
        "examples/deidentified-soul-profile.json",
        "examples/sample-mission.json",
        "PRIVACY.md",
        "SECURITY.md",
        "UNINSTALL.md",
        "CHANGELOG.md",
        "LICENSE.md",
        "SBOM-or-Dependency-Record.json",
        "base-pack/DISCOVER-Complete-AI-OS-Hermes-Installer.md",
        "base-pack/DISCOVER-Complete-AI-OS-Setup-Guide.md",
        "base-pack/DISCOVER-Complete-AI-OS-Setup-Guide.docx",
        "RELEASE-MANIFEST.json",
        "SHA256SUMS.txt",
    ]
    check(PACKAGE.is_dir(), "Package directory exists", PACKAGE)
    if not PACKAGE.is_dir():
        print(f"SUMMARY passed={PASSED} failed={FAILED}")
        raise SystemExit(1)
    for relative in required:
        path = PACKAGE / relative
        check(path.is_file() and path.stat().st_size > 0, f"Required artifact exists: {relative}")

    critical = [HTML, APP_JS, CSS, SERVER, PACKAGE / "VERSION"]
    if not all(path.is_file() for path in critical):
        print(f"SUMMARY passed={PASSED} failed={FAILED}")
        raise SystemExit(1)

    package_symlinks = [path.relative_to(PACKAGE).as_posix() for path in PACKAGE.rglob("*") if path.is_symlink()]
    check(not package_symlinks, "Package tree contains no symlinks", package_symlinks)
    package_files = sorted(
        [path for path in PACKAGE.rglob("*") if path.is_file() and not path.is_symlink()],
        key=lambda path: path.relative_to(PACKAGE).as_posix(),
    )
    relative_files = [path.relative_to(PACKAGE).as_posix() for path in package_files]
    check(len(relative_files) == len(set(relative_files)), "Package file inventory has unique relative names")

    check((PACKAGE / "VERSION").read_text(encoding="utf-8").strip() == VERSION, "VERSION is exactly 2.0.0")
    app = APP_JS.read_text(encoding="utf-8")
    html = HTML.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    server_source = SERVER.read_text(encoding="utf-8")
    check(f'const APP_VERSION = "{VERSION}"' in app, "Application JavaScript carries the exact release version")
    check("Mission Control v2.0.0" in html and "Nurse AI OS Mission Control" in html, "Dashboard identity and version are visible")
    check(f'product: "{HEALTH_PRODUCT}"' in server_source and f'version: "{VERSION}"' in server_source, "Server source carries exact health identity")
    check('const HOST = "127.0.0.1"' in server_source and "const PORT = 43127" in server_source, "Server is fixed to loopback-only origin")

    json_paths = sorted(PACKAGE.rglob("*.json"))
    parsed_json: dict[Path, Any] = {}
    for path in json_paths:
        value = read_json(path)
        if value is not None:
            parsed_json[path] = value
            check(True, f"JSON parses: {path.relative_to(PACKAGE).as_posix()}")
    check(len(parsed_json) == len(json_paths), "Every package JSON file parses", {"parsed": len(parsed_json), "expected": len(json_paths)})

    role_config = parsed_json.get(PACKAGE / "config" / "role-dashboards.json", {})
    mission_schema = parsed_json.get(PACKAGE / "config" / "mission.schema.json", {})
    evidence_schema = parsed_json.get(PACKAGE / "config" / "capability-evidence.schema.json", {})
    discover_schema = parsed_json.get(PACKAGE / "config" / "discover-packet-input.schema.json", {})
    soul_schema = parsed_json.get(PACKAGE / "config" / "soul-profile-input.schema.json", {})
    config_manifest = parsed_json.get(PACKAGE / "config" / "mission-control-manifest.json", {})
    edena = parsed_json.get(PACKAGE / "config" / "edena-policy.json", {})

    schema_expectations = {
        "discover-packet-input.schema.json": (discover_schema, "NAIO-DISCOVER-PACKET-ADAPTER-1"),
        "soul-profile-input.schema.json": (soul_schema, "NAIO-SOUL-PROFILE-ADAPTER-1"),
        "mission.schema.json": (mission_schema, "NAIO-MISSION-1"),
        "capability-evidence.schema.json": (evidence_schema, "NAIO-CAPABILITY-EVIDENCE-1"),
    }
    for filename, (schema, logical_id) in schema_expectations.items():
        check(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", f"{filename} declares JSON Schema 2020-12")
        check(schema.get("$id") == f"https://nurse-ai-os.local/schemas/{filename}", f"{filename} has the expected local schema URI")
        check(schema.get("properties", {}).get("schema", {}).get("const") == logical_id, f"{filename} carries logical schema id {logical_id}")
        refs: list[str] = []

        def collect_refs(value: Any) -> None:
            if isinstance(value, dict):
                if isinstance(value.get("$ref"), str):
                    refs.append(value["$ref"])
                for child in value.values():
                    collect_refs(child)
            elif isinstance(value, list):
                for child in value:
                    collect_refs(child)

        collect_refs(schema)
        unresolved = []
        for ref in refs:
            try:
                resolve_json_pointer(schema, ref)
            except (KeyError, TypeError, ValueError):
                unresolved.append(ref)
        check(not unresolved, f"{filename} has only resolvable internal references", unresolved)

    example_pairs = [
        ("deidentified-discover-packet.json", discover_schema),
        ("deidentified-soul-profile.json", soul_schema),
        ("sample-mission.json", mission_schema),
    ]
    for filename, schema in example_pairs:
        example = parsed_json.get(PACKAGE / "examples" / filename)
        errors = schema_errors(example, schema, schema) if example is not None and schema else ["missing example or schema"]
        check(not errors, f"{filename} validates against its bundled schema", errors[:12])
    discover_example = parsed_json.get(PACKAGE / "examples" / "deidentified-discover-packet.json", {})
    soul_example = parsed_json.get(PACKAGE / "examples" / "deidentified-soul-profile.json", {})
    mission_example = parsed_json.get(PACKAGE / "examples" / "sample-mission.json", {})
    check(discover_example.get("demo") is True and soul_example.get("demo") is True and mission_example.get("sample") is True, "All bundled examples are explicitly synthetic/demo")
    check(mission_example.get("artifactState") == "evaluated_outcome" and mission_example.get("missionStatus") == "completed", "Sample mission demonstrates the full evaluated loop")
    check(list(mission_example.get("stages", {})) == STAGES and all(mission_example.get("stages", {}).get(stage, {}).get("complete") is True for stage in STAGES), "Sample mission includes all five complete stages")

    app_role_ids = re.findall(r'\brole\("([a-z0-9-]+)"', app)
    configured_role_ids = [item.get("id") for item in role_config.get("roles", []) if isinstance(item, dict)]
    mission_role_ids = mission_schema.get("properties", {}).get("roleId", {}).get("enum", [])
    evidence_role_ids = evidence_schema.get("properties", {}).get("roleId", {}).get("enum", [])
    discover_role_ids = discover_schema.get("$defs", {}).get("roleId", {}).get("enum", [])
    role_sources = {
        "app": app_role_ids,
        "role config": configured_role_ids,
        "mission schema": mission_role_ids,
        "evidence schema": evidence_role_ids,
        "Discover schema": discover_role_ids,
    }
    check(all(ids == ROLE_IDS for ids in role_sources.values()), "All app/config/schema role inventories match the exact 17-role canonical order", role_sources)
    check(len(app_role_ids) == 17 and len(set(app_role_ids)) == 17, "Application exposes exactly 17 unique role recipes", app_role_ids)
    check(role_config.get("default_role_id") == "shared-identity" and configured_role_ids[:1] == ["shared-identity"], "Neutral shared identity is the default role")
    workflow_ids = {f"DSC-WF-{number:02d}" for number in range(1, 25)}
    role_workflows_valid = all(
        isinstance(role.get("recommended_workflow_ids"), list)
        and role.get("recommended_workflow_ids")
        and len(role["recommended_workflow_ids"]) == len(set(role["recommended_workflow_ids"]))
        and set(role["recommended_workflow_ids"]) <= workflow_ids
        for role in role_config.get("roles", [])
        if isinstance(role, dict)
    )
    check(role_workflows_valid, "Every role recipe recommends unique known workflow IDs")

    app_capability_ids = re.findall(r'\bcapability\("([a-z0-9-]+)"', app)
    evidence_capability_ids = evidence_schema.get("properties", {}).get("capabilityId", {}).get("enum", [])
    discover_capability_ids = discover_schema.get("$defs", {}).get("capabilityId", {}).get("enum", [])
    check(app_capability_ids == CAPABILITY_IDS and evidence_capability_ids == CAPABILITY_IDS and discover_capability_ids == CAPABILITY_IDS, "App and schemas carry the exact 17 capability pathways")
    workflow_numbers = [int(value) for value in re.findall(r"\bwf\((\d+),", app)]
    power_numbers = [int(value) for value in re.findall(r"\bpower\((\d+),", app)]
    template_block = re.search(r"const TEMPLATES = \[(.*?)\]\s*\.map", app, re.S)
    templates = re.findall(r'^\s*"(?:\\.|[^"\\])*"\s*,?\s*$', template_block.group(1), re.M) if template_block else []
    check(workflow_numbers == list(range(1, 25)), "Application contains exact ordered 24-workflow inventory", workflow_numbers)
    check(power_numbers == list(range(1, 25)), "Application contains exact ordered 24-SuperPower inventory", power_numbers)
    check(len(templates) == 30, "Application contains exact 30-template inventory", len(templates))
    check(f"const ARTIFACT_STATES = {json.dumps(ARTIFACT_STATES)}" in app, "Application carries exact ordered eight-state artifact lifecycle")

    schema_map = config_manifest.get("schemas", {})
    check(
        config_manifest.get("schema") == "NAIO-MISSION-CONTROL-MANIFEST-1"
        and config_manifest.get("product", {}).get("id") == PRODUCT_ID
        and config_manifest.get("product", {}).get("version") == VERSION,
        "Mission Control manifest has exact product identity",
        config_manifest.get("product"),
    )
    check(config_manifest.get("storage", {}).get("storage_key") == STORAGE_KEY and STORAGE_KEY in app, "Manifest and application use one exact storage key")
    check(
        schema_map.get("discover_packet", {}).get("id") == "NAIO-DISCOVER-PACKET-ADAPTER-1"
        and schema_map.get("soul_profile", {}).get("id") == "NAIO-SOUL-PROFILE-ADAPTER-1"
        and schema_map.get("mission", {}).get("id") == "NAIO-MISSION-1"
        and schema_map.get("capability_evidence", {}).get("id") == "NAIO-CAPABILITY-EVIDENCE-1",
        "Mission Control manifest binds all four logical schemas",
        schema_map,
    )
    check(config_manifest.get("runtime", {}).get("network_required") is False and config_manifest.get("runtime", {}).get("external_services") == [] and config_manifest.get("runtime", {}).get("direct_execution") is False, "Runtime manifest declares no network dependency or execution")
    check(
        f"{edena.get('id')}@{edena.get('version')}" == EDENA_POLICY
        and config_manifest.get("governance", {}).get("policy_id") == "EDENA-MC-ADVISORY"
        and config_manifest.get("governance", {}).get("policy_version") == "1.0.0-draft",
        "EDENA policy identity is consistent across governance configuration",
    )
    check(edena.get("artifact_state_order") == ARTIFACT_STATES and set(edena.get("tiers", {})) == {"unclassified", "green", "yellow", "orange", "red"}, "EDENA policy covers the exact artifact order and five classification states")

    audit = HtmlAudit()
    audit.feed(html)
    duplicate_ids = [identifier for identifier, count in Counter(audit.ids).items() if count > 1]
    missing_refs = sorted((set(audit.references) | set(audit.fragment_links)) - set(audit.ids))
    check(not duplicate_ids, "HTML IDs are unique", duplicate_ids)
    check(not missing_refs, "All static labels, ARIA references and fragment links resolve", missing_refs)
    check(audit.scripts == ["assets/app.js"] and audit.inline_scripts == 0, "HTML loads one expected local script and no inline scripts", {"scripts": audit.scripts, "inline": audit.inline_scripts})
    check(audit.styles == ["assets/styles.css"], "HTML loads one expected local stylesheet", audit.styles)
    check(not audit.remote_resources, "HTML has no remote resource or external-script dependency", audit.remote_resources)
    check(not audit.inline_handlers, "HTML contains no inline event-handler code", audit.inline_handlers)
    meta_csp = re.search(r'<meta\s+http-equiv="Content-Security-Policy"\s+content="([^"]+)"', html)
    csp_value = meta_csp.group(1) if meta_csp else ""
    check(all(value in csp_value for value in ("script-src 'self'", "connect-src 'none'", "object-src 'none'", "base-uri 'none'", "form-action 'none'")), "HTML meta Content Security Policy is fail-closed", csp_value)
    network_primitives = [token for token in ("fetch(", "XMLHttpRequest", "WebSocket", "EventSource", "sendBeacon", "navigator.serviceWorker") if token in app]
    check(not network_primitives, "Application contains no network client, telemetry or service-worker primitive", network_primitives)
    dynamic_code = [token for token in ("eval(", "new Function(", "document.write(") if token in app]
    check(not dynamic_code, "Application contains no dynamic-code execution primitive", dynamic_code)
    check(html.count('class="guide-number"') == 12, "Embedded Guide contains exact 12 numbered sections", html.count('class="guide-number"'))
    check("Start a Mission" in html and all(stage.title() in html for stage in STAGES), "Dashboard visibly exposes Start a Mission and the five-stage loop")
    check("Your Nurse AI OS Mission Control is being prepared." in html and "This process may take several minutes" in html, "First-run processing message includes the required preparation warning")
    check("AI supports—not replaces—professional judgment" in html and "hold no clinical license or accountability" in html, "Permanent accountability boundary is visible in the dashboard")
    check("@media (prefers-reduced-motion: reduce)" in css and ":focus-visible" in css, "CSS includes reduced-motion and visible-focus support")
    check("@media (max-width: 680px)" in css and "@media (max-width: 900px)" in css, "CSS includes mobile and compact responsive breakpoints")

    node = os.environ.get("CODEX_PRIMARY_RUNTIME_NODE") or shutil.which("node")
    check(bool(node and Path(node).is_file()), "Node.js runtime is available for syntax and loopback checks", node)
    if node:
        app_syntax = subprocess.run([node, "--check", str(APP_JS)], cwd=PACKAGE, capture_output=True, text=True)
        check(app_syntax.returncode == 0, "Application JavaScript passes syntax validation", app_syntax.stderr.strip())
        server_syntax = subprocess.run([node, "--check", str(SERVER)], cwd=PACKAGE, capture_output=True, text=True)
        check(server_syntax.returncode == 0, "Local server JavaScript passes syntax validation", server_syntax.stderr.strip())
        if server_syntax.returncode == 0:
            verify_server(node)

    for launcher_name in ("Start-DISCOVER.command", "start-discover.sh"):
        launcher = PACKAGE / launcher_name
        mode = stat.S_IMODE(launcher.stat().st_mode) if launcher.is_file() else 0
        check((mode & 0o111) == 0o111, f"{launcher_name} is executable for user, group and other", oct(mode))

    docx = PACKAGE / "base-pack" / "DISCOVER-Complete-AI-OS-Setup-Guide.docx"
    if docx.is_file():
        try:
            with zipfile.ZipFile(docx) as archive:
                bad_docx = archive.testzip()
                docx_names = archive.namelist()
                unsafe_docx = [name for name in docx_names if not safe_relative_name(name)]
            check(bad_docx is None and not unsafe_docx, "Optional legacy Word guide retains safe ZIP integrity", {"bad": bad_docx, "unsafe": unsafe_docx})
        except zipfile.BadZipFile as error:
            check(False, "Optional legacy Word guide retains safe ZIP integrity", error)

    check(DOM_QA.is_file(), "DOM interaction and accessibility QA report exists")
    if DOM_QA.is_file():
        dom = read_json(DOM_QA) or {}
        assertion_names = [item.get("name", "") for item in dom.get("assertions", []) if isinstance(item, dict) and item.get("passed") is True]
        check(dom.get("app") == "DISCOVER-NURSE-AI-OS-MISSION-CONTROL-2.0.0", "DOM QA targets the exact v2 product")
        check(dom.get("failed") == 0 and dom.get("passed", 0) >= 31, "DOM interaction and accessibility QA passes all checks", {"passed": dom.get("passed"), "failed": dom.get("failed")})
        check(any("17 role" in name for name in assertion_names) and any("Discover Packet" in name for name in assertion_names), "DOM QA covers the 17-role and Discover Packet architecture", assertion_names)
        check(not dom.get("runtime_errors"), "DOM QA recorded no runtime errors", dom.get("runtime_errors"))
        serious_dom_axe = [item for item in dom.get("axe", {}).get("violations", []) if item.get("impact") in {"critical", "serious"}]
        check(not serious_dom_axe, "DOM axe scan has no critical or serious violations", serious_dom_axe)

    check(VISUAL_QA.is_file(), "Real-browser visual QA report exists")
    if VISUAL_QA.is_file():
        visual = read_json(VISUAL_QA) or {}
        visual_names = [item.get("name", "") for item in visual.get("checks", []) if isinstance(item, dict) and item.get("passed") is True]
        summary = visual.get("summary", {})
        check(summary.get("failed") == 0 and summary.get("passed", 0) >= 29, "Desktop/mobile real-browser QA passes all checks", summary)
        check(len(visual.get("screenshots", [])) >= 12, "Visual QA captures first-run, desktop, adapters, mission, capabilities, guide and mobile evidence", len(visual.get("screenshots", [])))
        check(any("Discover Packet" in name for name in visual_names) and any("five" in name.lower() and "stage" in name.lower() for name in visual_names), "Visual QA covers Discover personalization and the five-stage mission loop", visual_names)
        check(not visual.get("console_errors"), "Real-browser QA recorded no console or page errors", visual.get("console_errors"))
        serious_visual_axe = [item for item in visual.get("axe", []) if item.get("impact") in {"critical", "serious"}]
        check(not serious_visual_axe, "Real-browser axe scan has no critical or serious violations", serious_visual_axe)

    release = parsed_json.get(RELEASE_MANIFEST, {})
    check(release.get("schema") == "NAIO-MISSION-CONTROL-RELEASE-2", "Release manifest has exact v2 schema identity", release.get("schema"))
    check(
        release.get("product_id") == PRODUCT_ID
        and release.get("hermes_companion_id") == HERMES_COMPANION_ID
        and release.get("version") == VERSION,
        "Release manifest has exact product, Hermes companion and version identity",
    )
    check(is_iso_datetime(release.get("generated_at")), "Release manifest has an offset-aware generation timestamp", release.get("generated_at"))
    check(release.get("catalog_counts") == EXPECTED_COUNTS, "Release manifest has exact architecture counts", release.get("catalog_counts"))
    check(release.get("integration", {}).get("network_calls_from_dashboard") == 0 and release.get("integration", {}).get("external_actions") is False and release.get("integration", {}).get("background_execution") is False, "Release manifest preserves local manual-handoff boundaries")
    check(release.get("governance", {}).get("edena_policy") == EDENA_POLICY and release.get("governance", {}).get("human_accountability") is True and release.get("governance", {}).get("badges_are_credentials") is False, "Release manifest preserves EDENA, accountability and noncredential boundaries")

    manifest_items = release.get("files_excluding_manifest_and_checksums", [])
    manifest_map: dict[str, dict[str, Any]] = {}
    manifest_safe = isinstance(manifest_items, list)
    if isinstance(manifest_items, list):
        for item in manifest_items:
            if not isinstance(item, dict) or set(item) != {"path", "bytes", "sha256"}:
                manifest_safe = False
                continue
            name = item.get("path")
            if not isinstance(name, str) or not safe_relative_name(name) or name in manifest_map:
                manifest_safe = False
                continue
            manifest_map[name] = item
    expected_manifest_names = set(relative_files) - {"RELEASE-MANIFEST.json", "SHA256SUMS.txt"}
    check(manifest_safe and set(manifest_map) == expected_manifest_names, "Release manifest safely covers every payload file exactly once", {"actual": len(manifest_map), "expected": len(expected_manifest_names)})
    manifest_hashes_ok = all(
        isinstance(item.get("bytes"), int)
        and item["bytes"] == (PACKAGE / name).stat().st_size
        and item.get("sha256") == sha256(PACKAGE / name)
        for name, item in manifest_map.items()
        if (PACKAGE / name).is_file()
    ) and set(manifest_map) == expected_manifest_names
    check(manifest_hashes_ok, "Every release-manifest size and SHA-256 digest verifies")

    checksum_map: dict[str, str] = {}
    checksum_safe = CHECKSUMS.is_file()
    if CHECKSUMS.is_file():
        for line in CHECKSUMS.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
            if not match:
                checksum_safe = False
                continue
            digest, name = match.groups()
            if not safe_relative_name(name) or name in checksum_map:
                checksum_safe = False
                continue
            checksum_map[name] = digest
    expected_checksum_names = set(relative_files) - {"SHA256SUMS.txt"}
    check(checksum_safe and set(checksum_map) == expected_checksum_names, "SHA256SUMS safely covers every package file except itself", {"actual": len(checksum_map), "expected": len(expected_checksum_names)})
    checksums_ok = set(checksum_map) == expected_checksum_names and all(sha256(PACKAGE / name) == digest for name, digest in checksum_map.items() if (PACKAGE / name).is_file())
    check(checksums_ok, "Every package SHA-256 checksum verifies")

    check(ZIP_PATH.is_file() and ZIP_ALIAS.is_file(), "Versioned release ZIP and stable alias both exist")
    if ZIP_PATH.is_file() and ZIP_ALIAS.is_file():
        check(sha256(ZIP_PATH) == sha256(ZIP_ALIAS), "Versioned ZIP and stable alias are byte-identical")
        try:
            with zipfile.ZipFile(ZIP_PATH) as archive:
                bad_zip = archive.testzip()
                infos = archive.infolist()
                names = [info.filename for info in infos]
                unsafe_names = [name for name in names if not safe_relative_name(name)]
                duplicate_names = [name for name, count in Counter(names).items() if count > 1]
                encrypted = [info.filename for info in infos if info.flag_bits & 1]
                symlink_members = [info.filename for info in infos if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK]
                directory_members = [info.filename for info in infos if info.is_dir()]
                expected_zip_names = {f"{PACKAGE.name}/{name}" for name in relative_files}
                zip_hashes_ok = all(
                    name in expected_zip_names
                    and sha256_bytes(archive.read(name)) == sha256(PACKAGE / name.removeprefix(f"{PACKAGE.name}/"))
                    for name in names
                    if name in expected_zip_names
                ) and set(names) == expected_zip_names
                zip_modes = {info.filename: stat.S_IMODE(info.external_attr >> 16) for info in infos}
            check(bad_zip is None, "Release ZIP passes CRC integrity", bad_zip)
            check(not unsafe_names and not duplicate_names and not encrypted and not symlink_members and not directory_members, "Release ZIP has no traversal, duplicates, encryption, symlinks or directory-only entries", {"unsafe": unsafe_names, "duplicates": duplicate_names, "encrypted": encrypted, "symlinks": symlink_members, "directories": directory_members})
            check(set(names) == expected_zip_names and len(names) == len(relative_files), "Release ZIP has exact rooted package-file coverage", {"zip": len(names), "package": len(relative_files)})
            check(zip_hashes_ok, "Every decompressed ZIP member matches the package SHA-256 digest")
            for launcher_name in ("Start-DISCOVER.command", "start-discover.sh"):
                member = f"{PACKAGE.name}/{launcher_name}"
                check((zip_modes.get(member, 0) & 0o111) == 0o111, f"ZIP preserves executable mode for {launcher_name}", oct(zip_modes.get(member, 0)))
        except (OSError, zipfile.BadZipFile, RuntimeError) as error:
            check(False, "Release ZIP opens safely", error)

    print(f"SUMMARY passed={PASSED} failed={FAILED}")
    if FAILED:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
