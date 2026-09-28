"""Load the synthetic sample manager week (NM-002).

Onboarding's "try the sample manager brief" step. The sample workspace is
marked ``sample`` so every view and every rendered brief says it is
synthetic; it can be deleted like any other workspace directory.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from . import resources
from .services import ManagerWorkspace
from .store import utc_now

SAMPLE_PATH = resources.manager_root() / "samples" / "synthetic-week.json"


def load_sample(
    root: Path, *, sample_path: Path = SAMPLE_PATH, clock: Callable[[], str] = utc_now
) -> tuple[ManagerWorkspace, dict[str, Any]]:
    data = json.loads(Path(sample_path).read_text(encoding="utf-8"))
    if not data.get("synthetic"):
        raise ValueError("the sample loader only loads data marked synthetic")
    ws = ManagerWorkspace(root, clock=clock)
    ws.create(data["workspace"]["name"], data["workspace"]["owner"], sample=True)

    projects = {
        p["key"]: ws.add_project(p["title"], p["purpose"], p["owner"], p.get("next_milestone", ""))
        for p in data["projects"]
    }
    for t in data["tasks"]:
        status = t.get("status", "idea")
        task_id = ws.add_task(
            t["title"], t["owner"],
            project_id=projects.get(t.get("project")),
            due_date=t.get("due_date"),
            status="ready" if status == "completed" else status,
            reviewer=t.get("reviewer", ""),
            next_action=t.get("next_action", ""),
        )
        if t.get("blocked_reason"):
            ws.set_blocked(task_id, True, t["blocked_reason"])
        if status == "completed":
            ws.complete_task(task_id, t["evidence"])
    for d in data["decisions"]:
        ws.record_decision(
            d["question"], d["decision"], d["decided_by"], d["decided_on"],
            rationale=d.get("rationale", ""), project_id=projects.get(d.get("project")),
        )
    for s in data["sources"]:
        ws.add_source(
            s["title"], s["kind"], s["reference"], data_class=s["data_class"],
            project_id=projects.get(s.get("project")), review_date=s.get("review_date"),
        )
    for s in data.get("library", []):  # sources not tied to one project
        ws.add_source(s["title"], s["kind"], s["reference"], data_class=s["data_class"],
                      review_date=s.get("review_date"))
    for f in data.get("feedback", []):
        ws.add_feedback(projects[f["project"]], f["from"], f["kind"], f["summary"],
                        f["received_on"])
    ws.set_priorities(
        data["week_of"],
        [p["text"] for p in data["priorities"]],
        [projects.get(p.get("project")) for p in data["priorities"]],
    )
    return ws, data
