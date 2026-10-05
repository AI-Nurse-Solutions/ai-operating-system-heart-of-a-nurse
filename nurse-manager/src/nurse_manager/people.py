# Copyright 2026 Robert Domondon
# SPDX-License-Identifier: Apache-2.0
"""Controlled people labels, never identity verification or a text classifier."""
import json
from . import resources

RULES = json.loads((resources.manager_root() / "config" / "people-fields.json").read_text(encoding="utf-8"))
POLICY = RULES["policy"]
DATA_RULE = RULES["data_rule"]
LABELS = tuple(RULES["labels"])
_CANONICAL = {label.casefold(): label for label in LABELS}


def label(value, *, optional=False, self_only=False):
    if not isinstance(value, str):
        raise ValueError("choose a role label")
    value = value.strip()
    if not value and optional:
        return ""
    canonical = _CANONICAL.get(value.casefold())
    if canonical is None or (self_only and canonical != "me"):
        raise ValueError("choose a role label")
    return canonical


def shared_labels(value):
    if not isinstance(value, str) or len(value) > 200:
        raise ValueError("choose role labels")
    parts = value.split(";")
    if not 1 <= len(parts) <= RULES["max_shared_labels"]:
        raise ValueError("choose a bounded set of role labels")
    labels = [label(part) for part in parts]
    if len(set(labels)) != len(labels):
        raise ValueError("choose each role once")
    return "; ".join(labels)


def status(conn, workspace_id):
    """Count fields outside current labels, without asserting when they arose."""
    unknown = 0
    fields = (("workspaces", "owner", False, True), ("projects", "owner", False, False),
              ("tasks", "owner", False, False), ("tasks", "reviewer", True, False),
              ("decisions", "decided_by", False, False),
              ("project_feedback", "from_group", False, False),
              ("contributions", "shared_credit", False, False))
    for table, field, optional, self_only in fields:
        where = "id" if table == "workspaces" else "workspace_id"
        # Identifiers are internal constants; supplied ids remain parameters.
        for row in conn.execute(f"SELECT {field} FROM {table} WHERE {where} = ?", (workspace_id,)):
            try:
                if field == "shared_credit":
                    shared_labels(row[0])
                else:
                    label(row[0], optional=optional, self_only=self_only)
            except ValueError:
                unknown += 1
    return {"policy": POLICY, "unrecognized_fields": unknown}
