from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from .ledger import ProvenanceLedger
from .runtime_gate import RuntimeGate


def dataset_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_evaluations(root: Path, dataset_path: Path | None = None) -> dict[str, Any]:
    dataset_path = dataset_path or root / "evals" / "cases.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    if not dataset.get("synthetic_only"):
        raise ValueError("evaluation dataset must be synthetic_only")
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        ledger_path = Path(tmp) / "evaluation-ledger.jsonl"
        for case in dataset["cases"]:
            gate = RuntimeGate(
                root,
                log_path=ledger_path,
                runtime_config_path=root / "config" / case["config"],
                mode="evaluation",
            )
            event = gate.evaluate(case["tool"], case.get("args", {}))
            gate._append(event)
            actual = event["decision"]
            results.append({
                "id": case["id"],
                "expected": case["expected"],
                "actual": actual,
                "passed": actual == case["expected"],
                "reason_code": event["reason_code"],
            })
        ledger = ProvenanceLedger(ledger_path).verify()
    failures = [item for item in results if not item["passed"]]
    return {
        "dataset_id": dataset["dataset_id"],
        "dataset_version": dataset["dataset_version"],
        "dataset_hash": dataset_hash(dataset_path),
        "synthetic_only": True,
        "case_count": len(results),
        "passed": len(results) - len(failures),
        "failed": len(failures),
        "ok": not failures,
        "terminal_provenance_root": ledger["terminal_hash"],
        "results": results,
    }
