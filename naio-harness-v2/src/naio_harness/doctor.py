from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .capabilities import compile_capabilities, load_manifests
from .config_store import load_runtime_config
from .models import CapabilityLayer, CompilationContext


def run_doctor(root: Path) -> dict[str, Any]:
    config = load_runtime_config(root / "config" / "runtime-profile.json")
    manifests = load_manifests(root / "manifests")
    layers = [
        CapabilityLayer(
            name=item["name"],
            allow=None if item["allow"] is None else frozenset(item["allow"]),
            deny=frozenset(item["deny"]),
        )
        for item in config["layers"]
    ]
    context = CompilationContext(
        profile=config["profile"],
        audience=config["audience"],
        channel_trust=config["channel_trust"],
        provider=config["provider"],
        sandbox=config["sandbox"],
        no_phi=bool(config["no_phi"]),
        self_service=bool(config["self_service"]),
        gate_attested=bool(config["gate_attested"]),
    )
    result = compile_capabilities(manifests, set(config["enabled_capabilities"]), layers, context)
    return {
        "status": "ready" if result.ok else "blocked",
        "schema_version": config["schema_version"],
        "profile": config["profile"],
        "audience": config["audience"],
        "no_phi": config["no_phi"],
        "gate_attested": config["gate_attested"],
        "manifest_count": len(manifests),
        "compilation": result.as_dict(),
        "no_mutation": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only NAIO effective-policy attestation")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run_doctor(args.root)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"NAIO doctor: {report['status']}")
        print(f"profile={report['profile']} audience={report['audience']} no_phi={report['no_phi']}")
        print("effective=" + ", ".join(report["compilation"]["effective"]))
        for reason, values in report["compilation"]["removed"].items():
            print(f"removed[{reason}]=" + ", ".join(values))
    return 0 if report["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
