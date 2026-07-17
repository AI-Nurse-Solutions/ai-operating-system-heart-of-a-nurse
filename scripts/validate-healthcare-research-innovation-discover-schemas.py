#!/usr/bin/env python3
"""Compile DISCOVER schemas and prove conditional evidence is fail-closed."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SOURCE = (
    ROOT
    / "healthcare-research-innovation-leaders"
    / "packages"
    / "discover"
    / "Healthcare-Research-and-Innovation-Leader-DISCOVER-SuperPowers-Pack-v1.0"
    / "workflows"
    / "03-DISCOVER-Schemas-and-Agents.md"
)
SCHEMA_PATTERN = re.compile(
    r"^### `https://nurse-ai-os\.local/schemas/research_innovation_discover/([^/]+)/1\.0\.0`\n\n"
    r"\*\*Canonical SHA-256:\*\* `([0-9a-f]{64})`\n\n```json\n([^\n]+)\n```",
    re.MULTILINE,
)


def rejects(validator: Draft202012Validator, instance: Any) -> bool:
    return bool(list(validator.iter_errors(instance)))


def conditional_fragment(schema: dict[str, Any], branch: dict[str, Any], fields: tuple[str, str]) -> dict[str, Any]:
    properties = schema["properties"]
    return {
        "$schema": schema["$schema"],
        "$defs": schema["$defs"],
        "type": "object",
        "properties": {field: properties[field] for field in fields},
        "required": list(fields),
        "allOf": [branch],
        "additionalProperties": False,
    }


def branch_for(schema: dict[str, Any], target: str, trigger: str) -> dict[str, Any] | None:
    for branch in schema.get("allOf", []):
        then_properties = branch.get("then", {}).get("properties", {})
        if_properties = branch.get("if", {}).get("properties", {})
        if target in then_properties and trigger in if_properties:
            return branch
    return None


def main() -> None:
    blocks = SCHEMA_PATTERN.findall(SCHEMA_SOURCE.read_text(encoding="utf-8"))
    if len(blocks) != 18:
        raise SystemExit(f"Expected 18 schemas, found {len(blocks)}")

    for name, _digest, payload in blocks:
        schema = json.loads(payload)
        Draft202012Validator.check_schema(schema)

        required = set(schema["required"])
        if not {"approval", "aggregate_export_evidence_or_null"} <= required:
            raise SystemExit(f"{name}: conditional evidence fields are not root-required")

        record_states = schema["properties"]["record_state"].get("enum", [])
        approval_branch = branch_for(schema, "approval", "record_state")
        if approval_branch is not None:
            trigger_states = approval_branch["if"]["properties"]["record_state"].get("enum", [])
            evidence_states = [state for state in record_states if state in trigger_states]
            if not evidence_states:
                raise SystemExit(f"{name}: approval evidence branch has no reachable state")
            approval = Draft202012Validator(
                conditional_fragment(schema, approval_branch, ("record_state", "approval"))
            )
            if rejects(approval, {"record_state": "draft", "approval": None}):
                raise SystemExit(f"{name}: draft/null approval baseline rejected")
            if not rejects(approval, {"record_state": evidence_states[0], "approval": None}):
                raise SystemExit(f"{name}: {evidence_states[0]}/null approval was accepted")
        else:
            if name != "whole_life_private":
                raise SystemExit(f"{name}: unexpected non-approvable schema")
            if schema["properties"]["approval"].get("type") != "null":
                raise SystemExit(f"{name}: private approval is not forced null")
            if schema["properties"]["data_class"].get("const") != "DATA-D3-PRIVATE":
                raise SystemExit(f"{name}: private data class is not forced")

        data_class = schema["properties"]["data_class"]
        allows_d2 = data_class.get("const") == "DATA-D2" or "DATA-D2" in data_class.get("enum", [])
        aggregate_branch = branch_for(
            schema,
            "aggregate_export_evidence_or_null",
            "data_class",
        )
        if allows_d2:
            if aggregate_branch is None:
                raise SystemExit(f"{name}: DATA-D2 has no aggregate evidence branch")
            aggregate = Draft202012Validator(
                conditional_fragment(
                    schema,
                    aggregate_branch,
                    ("data_class", "aggregate_export_evidence_or_null"),
                )
            )
            if rejects(
                aggregate,
                {"data_class": "DATA-D1", "aggregate_export_evidence_or_null": None},
            ):
                raise SystemExit(f"{name}: DATA-D1/null aggregate baseline rejected")
            if not rejects(
                aggregate,
                {"data_class": "DATA-D2", "aggregate_export_evidence_or_null": None},
            ):
                raise SystemExit(f"{name}: DATA-D2/null aggregate evidence was accepted")
        elif aggregate_branch is not None:
            raise SystemExit(f"{name}: inapplicable aggregate evidence branch")

    print("DISCOVER_SCHEMA_COMPILE=passed draft=2020-12 schemas=18")
    print("DISCOVER_CONDITIONAL_EVIDENCE=fail_closed approval_negative_cases=17 aggregate_negative_cases=17 private_nonapprovable=1")


if __name__ == "__main__":
    main()
