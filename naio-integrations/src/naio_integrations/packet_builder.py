"""Installable role-packet bundles (Mission Control spec section 14).

Phase 2 of the release sequence: the first role packets — pre-licensure
student, staff nurse, and educator/preceptor/mentor. A bundle turns a
packet directory from a manifest into something independently useful
immediately after installation:

* ``manifest.json``      — the verified, checksummed packet manifest
* ``README.md``          — the section 19 recognitions: who this is for,
  what it helps accomplish, what it will never do on its own, what to do
  next, how work and data are protected, how progress is measured
* ``DATA-BOUNDARY.md``   — the prohibited-data notice every packet must
  show before first use (section 16 acceptance criterion)
* ``templates/``         — working starter templates rendered by the
  Deliverable Studio, each born a draft with the mandatory banner

No empty demo: every bundle opens with working templates, guidance, and
a first-run pathway pointer. Everything is deterministic — same catalog
in, byte-identical bundle out — so committed bundles rebuild exactly in
CI.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .deliverables import DeliverableStudio
from .packets import PacketCatalog, render_manifest, verify_manifest

PHASE_2_ROLES = ("pre-licensure-student", "staff-nurse", "educator")


class PacketBundleBuilder:
    """Assembles installable packet bundles from the reviewed catalog."""

    def __init__(
        self,
        catalog: PacketCatalog | None = None,
        studio: DeliverableStudio | None = None,
    ):
        self.catalog = catalog or PacketCatalog()
        self.studio = studio or DeliverableStudio()

    def build(self, role: str, target_dir: Path) -> list[Path]:
        manifest = self.catalog.build_manifest(role)
        verify_manifest(manifest)
        packet_config = self.catalog.catalog["packets"][role]
        target_dir.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []

        manifest_path = target_dir / "manifest.json"
        manifest_path.write_text(render_manifest(manifest), encoding="utf-8")
        written.append(manifest_path)

        readme_path = target_dir / "README.md"
        readme_path.write_text(
            self._render_readme(manifest, packet_config), encoding="utf-8"
        )
        written.append(readme_path)

        boundary_path = target_dir / "DATA-BOUNDARY.md"
        boundary_path.write_text(self._render_boundary(manifest), encoding="utf-8")
        written.append(boundary_path)

        templates_dir = target_dir / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        for template_id in packet_config.get("starter_templates", ()):
            scaffold = self.studio.scaffold(template_id)
            template_path = templates_dir / f"{template_id}.md"
            template_path.write_text(scaffold.body_markdown, encoding="utf-8")
            written.append(template_path)
        return written

    def build_phase2(self, packets_root: Path) -> list[Path]:
        written: list[Path] = []
        for role in PHASE_2_ROLES:
            written.extend(self.build(role, packets_root / role))
        return written

    # ------------------------------------------------------------------

    def _render_readme(
        self, manifest: dict[str, Any], packet_config: dict[str, Any]
    ) -> str:
        display = manifest["display_name"]
        role_modules = [
            module
            for module in manifest["role_modules"]
            if module not in self.catalog.catalog["shared_modules"]
        ]
        agents = [agent["agent_id"] for agent in manifest["default_agents"]]
        templates = packet_config.get("starter_templates", ())
        governance = manifest["governance"]
        lines = [
            f"# {display} — Mission Control Packet",
            "",
            f"Packet `{manifest['packet_name']}` v{manifest['packet_version']}"
            f" · {governance['directive']}",
            "",
            "## Who this workspace is for",
            "",
            f"A {display.lower()} using Nurse AI OS as a governed professional"
            " environment. One identity can hold this role alongside others —"
            " roles are lenses, never separate accounts.",
            "",
            "## What it helps you accomplish",
            "",
        ]
        lines += [f"- {module.replace('-', ' ').capitalize()}" for module in role_modules]
        lines += [
            "",
            "## What it will never do on its own",
            "",
            "It does not independently diagnose, prescribe, place clinical"
            " orders, modify a medical record, contact a patient, or execute"
            " a consequential institutional action. Agents propose; humans"
            " judge; nurses steward. Every starter agent ships tools-disabled"
            " and propose-only at the Green tier, with review required on"
            " every output.",
            "",
            "## What to do next",
            "",
            "1. Read `DATA-BOUNDARY.md` before first use.",
            "2. Open the shared example workspace"
            " (`mission-control/example-workspace/`) to see a completed,"
            " fully synthetic project.",
            "3. Create your first real artifact from `templates/` — every"
            " template opens as an editable draft with guidance in place:",
        ]
        lines += [f"   - `templates/{template_id}.md`" for template_id in templates]
        lines += [
            "4. Set your review cadence: daily focus, weekly review, monthly"
            " outcomes, quarterly capability and impact review.",
            "",
            "## How your work and data are protected",
            "",
            f"- Default risk tier: {governance['default_risk_tier']};"
            f" default data zone: {governance['default_data_zone']}.",
            f"- Prohibited data classes:"
            f" {', '.join(manifest['prohibited_data_classes'])}."
            f" {manifest['prohibited_data_note']}",
            "- Default permissions start empty and integrations are off until"
            " you enable them deliberately.",
            f"- Starter agents ({', '.join(agents)}) are inspectable,"
            " interruptible, and permission-bound, with a visible stop"
            " control.",
            f"- {governance['install_note']}",
            "",
            "## How progress is measured",
            "",
            "By demonstrated outputs and real-world impact — capability"
            " gained, time and friction reduced, quality and safety"
            " improved, opportunity created — never by surveillance scores"
            " or hidden rankings. Private reflections stay private.",
            "",
        ]
        return "\n".join(lines)

    def _render_boundary(self, manifest: dict[str, Any]) -> str:
        governance = manifest["governance"]
        return "\n".join(
            [
                "# Data Boundary Notice",
                "",
                "Read this before first use.",
                "",
                f"**Prohibited data classes:"
                f" {', '.join(manifest['prohibited_data_classes'])}.**",
                f"{manifest['prohibited_data_note']}",
                "",
                "- Do not enter patient names, medical record numbers, room"
                " and bed combinations, encounter dates, or any information"
                " that could identify a patient, colleague, or student.",
                "- The privacy screen redacts identifiers it recognizes, but"
                " detection reduces risk — it never proves content is"
                " de-identified or safe for unrestricted use.",
                f"- Work starts at the {governance['default_risk_tier']} tier"
                f" in the {governance['default_data_zone']} data zone;"
                " authority increases only through explicit controls and"
                " named human accountability.",
                "- Private reflections never appear in manager, faculty,"
                " cohort, or executive views, and content never moves between"
                " data zones without an explicit, recorded approval.",
                "- A stop control is always available; all agents can be"
                " paused globally.",
                "",
                f"{governance['install_note']}",
                "",
            ]
        )
