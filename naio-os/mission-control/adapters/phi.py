"""
The PHI shapes, in one place.

Three files needed this list — the server's lint, the SOUL importer's refusal,
and `naio-mc configure`'s path check — and each grew its own copy. They drifted:
the importer refused `MRN 123` while the server's lint accepted it, and the
`configure` copy never learned the explicit-DOB rule at all. A detection control
that means something different depending on which door you came through is not a
control, so all three now import this.

The bounds are deliberate:

  * MRN needs three or more digits. The importer's stricter reading wins over
    the server's four, because refusing a real record number matters more than
    the occasional false positive on 'MRN 12'.
  * Room and bed numbers stop at four digits plus an optional bed letter.
  * Date-of-birth catches both slash and dash forms, and the explicit label.

Detection, not prevention. It says 'this looks like PHI' loudly; it cannot
promise a file is clean, and nothing here should be read as if it could.
"""

from __future__ import annotations

PHI_PATTERNS: list[tuple[str, str]] = [
    (r"\bMRN[:#_\- ]?\s*\d{3,}\b", "medical record number"),
    (r"\b\d{3}-\d{2}-\d{4}\b", "SSN-shaped number"),
    (r"\b(?:0?[1-9]|1[0-2])[/\-_.](?:0?[1-9]|[12]\d|3[01])[/\-_.](?:19|20)\d{2}\b",
     "date of birth format"),
    (r"\b(?:room|rm|bed)\s*[#_\- ]?\s*\d{1,4}[A-Da-d]?\b", "room or bed number"),
    (r"\bDOB[:\s]", "explicit DOB label"),
]
