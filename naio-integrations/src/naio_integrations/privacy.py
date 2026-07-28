"""Privacy-transformation reference adapter (pattern: microsoft/presidio).

The privacy front door. Text is analyzed against configurable recognizers
(including healthcare-specific ones: MRN, room/bed, encounter dates,
provider identifiers) and transformed before it reaches a model, a memory
store, a log line, or an export.

Findings carry only entity type and span — never the matched raw value —
so the privacy layer itself cannot leak what it detected.

Detection reduces risk. It does not prove content is de-identified,
HIPAA-compliant, or safe for unrestricted use.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .contract import PrivacyFinding, PrivacyResult, PrivacyTransformationInterface

DEFAULT_RECOGNIZER_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "privacy-recognizers.json"
)


class PrivacyScreen(PrivacyTransformationInterface):
    """Deterministic recognizer-based privacy transformer."""

    def __init__(self, recognizer_path: Path | None = None):
        path = recognizer_path or DEFAULT_RECOGNIZER_PATH
        config = json.loads(path.read_text(encoding="utf-8"))
        self.recognizers = [
            {
                "name": item["name"],
                "entity_type": item["entity_type"],
                "pattern": re.compile(item["pattern"], re.IGNORECASE),
                "score": float(item["score"]),
            }
            for item in config["recognizers"]
        ]

    def analyze(self, text: str) -> tuple[PrivacyFinding, ...]:
        findings: list[PrivacyFinding] = []
        for recognizer in self.recognizers:
            for match in recognizer["pattern"].finditer(text):
                findings.append(
                    PrivacyFinding(
                        entity_type=recognizer["entity_type"],
                        start=match.start(),
                        end=match.end(),
                        score=recognizer["score"],
                        recognizer=recognizer["name"],
                    )
                )
        findings.sort(key=lambda finding: (finding.start, -finding.end))
        return tuple(findings)

    def transform(self, text: str, mode: str = "redact") -> PrivacyResult:
        findings = self.analyze(text)
        if not findings:
            return PrivacyResult(transformed_text=text, findings=(), action="pass")
        if mode == "block":
            return PrivacyResult(transformed_text="", findings=findings, action="block")
        pieces: list[str] = []
        cursor = 0
        for finding in findings:
            if finding.start < cursor:
                # Overlapping finding: never emit its tail — extend the
                # redacted region instead of leaking text past the cursor.
                cursor = max(cursor, finding.end)
                continue
            pieces.append(text[cursor:finding.start])
            pieces.append(f"<{finding.entity_type}>")
            cursor = finding.end
        pieces.append(text[cursor:])
        return PrivacyResult(
            transformed_text="".join(pieces), findings=findings, action="redact"
        )
