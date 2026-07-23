from __future__ import annotations

import hashlib
import json
import shutil
import stat
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
DELIVERABLES = ROOT / "deliverables"
PACKAGE = DELIVERABLES / "DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0"
ZIP_PATH = DELIVERABLES / "DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0.zip"
ZIP_ALIAS = DELIVERABLES / "DISCOVER-Nurse-AI-OS-Mission-Control.zip"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def regular_files() -> list[Path]:
    files: list[Path] = []
    for path in PACKAGE.rglob("*"):
        if path.is_symlink():
            raise SystemExit(f"Refusing symlink in package: {path}")
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(PACKAGE).as_posix())


def validate_json_files() -> None:
    for path in PACKAGE.rglob("*.json"):
        if path.name == "RELEASE-MANIFEST.json":
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise SystemExit(f"Invalid JSON file {path}: {error}") from error


def main() -> None:
    if not PACKAGE.is_dir():
        raise SystemExit(f"Missing package directory: {PACKAGE}")

    required = [
        "README-FIRST.md",
        "README.md",
        "VERSION",
        "index.html",
        "assets/app.js",
        "assets/styles.css",
        "server.mjs",
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
        "examples/deidentified-soul-profile.json",
        "examples/deidentified-discover-packet.json",
        "examples/sample-mission.json",
        "PRIVACY.md",
        "SECURITY.md",
        "UNINSTALL.md",
        "CHANGELOG.md",
        "LICENSE.md",
        "SBOM-or-Dependency-Record.json",
    ]
    missing = [relative for relative in required if not (PACKAGE / relative).is_file()]
    if missing:
        raise SystemExit(f"Missing required release files: {missing}")
    if (PACKAGE / "VERSION").read_text(encoding="utf-8").strip() != "2.0.0":
        raise SystemExit("VERSION must be exactly 2.0.0")

    for launcher in [PACKAGE / "Start-DISCOVER.command", PACKAGE / "start-discover.sh"]:
        launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    manifest_path = PACKAGE / "RELEASE-MANIFEST.json"
    checksum_path = PACKAGE / "SHA256SUMS.txt"
    manifest_path.unlink(missing_ok=True)
    checksum_path.unlink(missing_ok=True)
    validate_json_files()

    payload_files = regular_files()
    manifest = {
        "schema": "NAIO-MISSION-CONTROL-RELEASE-2",
        "product": "DISCOVER · Nurse AI OS Mission Control",
        "product_id": "discover-nurse-ai-os-mission-control",
        "hermes_companion_id": "NAIOS-MISSION-CONTROL-LOCAL-2.0.0",
        "version": "2.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "integration": {
            "host": "Hermes-powered Nurse AI OS",
            "mode": "downloaded local static application with manual reviewed handoffs",
            "background_execution": False,
            "network_calls_from_dashboard": 0,
            "external_actions": False,
            "institutional_policy_mode": "preview only; not managed or tamper-resistant enforcement",
        },
        "catalog_counts": {
            "roles": 17,
            "powers": 24,
            "workflows": 24,
            "templates": 30,
            "mission_stages": 5,
            "artifact_states": 8,
            "capabilities": 17,
            "mastery_levels": 4,
            "guide_sections": 12,
        },
        "soul_profile": {
            "adapter_schema": "NAIO-SOUL-PROFILE-ADAPTER-1",
            "quiz_definition_status": "provisional and replaceable",
            "raw_answers_imported_or_persisted": False,
            "neutral_mode_supported": True,
        },
        "discover_packet": {
            "adapter_schema": "NAIO-DISCOVER-PACKET-ADAPTER-1",
            "input_status": "derived non-sensitive configuration only; raw notes prohibited",
            "neutral_mode_supported": True,
        },
        "governance": {
            "edena_policy": "EDENA-MC-ADVISORY@1.0.0-draft",
            "personal_red": "prominent advisory plus deliberate acknowledgment; sanitized exploration only",
            "institutional_red": "blocked transition in local policy preview; real enforcement requires a managed edition",
            "human_accountability": True,
            "badges_are_credentials": False,
        },
        "privacy": {
            "browser_storage_encrypted": False,
            "session_only_missions_persisted": False,
            "explicit_backup_may_contain_mission_text": True,
            "prohibited_data": ["PHI", "confidential institutional information", "credentials", "secrets"],
        },
        "compatibility": {
            "browser": "current desktop browser with JavaScript and localStorage",
            "optional_local_server": "Node.js 18 or newer",
            "portable_mode": "index.html; separate browser-storage origin from server mode",
        },
        "files_excluding_manifest_and_checksums": [
            {
                "path": path.relative_to(PACKAGE).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in payload_files
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checksum_files = [path for path in regular_files() if path != checksum_path]
    checksum_path.write_text(
        "".join(f"{sha256(path)}  {path.relative_to(PACKAGE).as_posix()}\n" for path in checksum_files),
        encoding="utf-8",
    )

    final_files = regular_files()
    ZIP_PATH.unlink(missing_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in final_files:
            relative = PurePosixPath(PACKAGE.name) / PurePosixPath(path.relative_to(PACKAGE).as_posix())
            info = zipfile.ZipInfo.from_file(path, arcname=relative.as_posix())
            info.compress_type = zipfile.ZIP_DEFLATED
            with path.open("rb") as handle:
                archive.writestr(info, handle.read(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    shutil.copy2(ZIP_PATH, ZIP_ALIAS)
    print(ZIP_PATH)
    print(ZIP_ALIAS)
    print(f"package_files={len(final_files)}")
    print(f"checksum_entries={len(checksum_files)}")
    print(f"zip_sha256={sha256(ZIP_PATH)}")


if __name__ == "__main__":
    main()
