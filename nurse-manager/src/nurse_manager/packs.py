"""Education, committee, and communication packs (build step 5.4).

A pack is a small, reviewed set of document templates for one part of a
manager's work. Its manifest (``nurse-manager/packs/<id>.json``) says:

* **who maintains it** and **when it was last reviewed and must be
  reviewed again.** A pack past its review date is still shown, but no new
  document can be started from it until it is reviewed.
* **exactly which templates it uses.** The templates live once, in the
  shared deliverable catalog (``naio-integrations``), and are reused, never
  copied. The manifest pins each one by the sha256 of its content, so a
  template that changes without the pack being reviewed again is refused.
* **the rules that come with it**, shown in every document started from it.

A document started from a pack is a draft like the weekly brief: the
manager edits it, and accepts exactly the text they reviewed. Starting one
writes the template's headings and guidance, and nothing else: no model,
and nothing taken from the records except the project the manager chose.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from . import resources
from .brief import BriefService, Revision, StaleRevision
from .services import ManagerError, ManagerWorkspace
from .store import new_id

PACK_SCHEMA = "nurse-manager-pack@1"
PACK_ID = re.compile(r"[a-z][a-z0-9-]{1,39}")
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
MAX_DOCUMENT_CHARS = 50_000

PACK_DRAFT_BANNER = (
    "> **DRAFT — started from a pack template.** Not accepted. Write each"
    " section yourself, check it, and accept it before it is used anywhere;"
    " a template never makes a document final."
)


class PackError(ManagerError):
    """A pack that cannot be used, or a request a pack refuses."""


def packs_dir() -> Path:
    return resources.manager_root() / "packs"


def template_sha256(spec: dict[str, Any]) -> str:
    """The pin for one catalog template: sha256 of its canonical JSON."""
    canonical = json.dumps(spec, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _catalog() -> dict[str, Any]:
    return json.loads(resources.naio_config("deliverable-templates.json").read_text("utf-8"))


def load_pack(path: Path, catalog: dict[str, Any]) -> dict[str, Any]:
    """Read and check one manifest. Raises PackError saying what is wrong."""
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PackError(f"{path.name}: not a readable pack manifest") from exc
    if not isinstance(manifest, dict) or manifest.get("schema") != PACK_SCHEMA:
        raise PackError(f"{path.name}: not a {PACK_SCHEMA} manifest")
    pack_id = manifest.get("id")
    if not isinstance(pack_id, str) or not PACK_ID.fullmatch(pack_id) or path.stem != pack_id:
        raise PackError(f"{path.name}: the pack id must match its file name")
    for key in ("title", "purpose", "maintainer"):
        if not isinstance(manifest.get(key), str) or not manifest[key].strip():
            raise PackError(f"pack {pack_id}: {key} is required")
    if not isinstance(manifest.get("version"), str) or not VERSION.fullmatch(manifest["version"]):
        raise PackError(f"pack {pack_id}: version must look like 1.0.0")
    try:
        reviewed = date.fromisoformat(manifest.get("reviewed_on") or "")
        due = date.fromisoformat(manifest.get("review_by") or "")
    except (TypeError, ValueError) as exc:
        raise PackError(f"pack {pack_id}: reviewed_on and review_by must be dates") from exc
    if due <= reviewed:
        raise PackError(f"pack {pack_id}: review_by must come after reviewed_on")
    source = manifest.get("catalog")
    if not isinstance(source, dict) or source.get("schema_version") != catalog.get("schema_version"):
        raise PackError(f"pack {pack_id}: it was reviewed against a different template catalog")
    templates = manifest.get("templates")
    if not isinstance(templates, dict) or not templates:
        raise PackError(f"pack {pack_id}: it lists no templates")
    for template_id, pinned in templates.items():
        spec = catalog["templates"].get(template_id)
        if spec is None:
            raise PackError(f"pack {pack_id}: template {template_id} is not in the catalog")
        if template_sha256(spec) != pinned:
            raise PackError(f"pack {pack_id}: template {template_id} changed since the pack"
                            " was reviewed; review the pack again")
    rules = manifest.get("rules")
    if not isinstance(rules, list) or not rules or not all(
            isinstance(rule, str) and rule.strip() for rule in rules):
        raise PackError(f"pack {pack_id}: it needs at least one rule")
    return manifest


def available_packs(today: str) -> list[dict[str, Any]]:
    """Every shipped pack, checked, with whether it may be used on ``today``.

    A pack that fails its checks is listed as unavailable with the reason,
    never silently dropped and never used.
    """
    catalog = _catalog()
    packs = []
    for path in sorted(packs_dir().glob("*.json")):
        try:
            manifest = load_pack(path, catalog)
        except PackError as exc:
            packs.append({"id": path.stem, "status": "unavailable", "reason": str(exc)})
            continue
        overdue = manifest["review_by"] < today
        packs.append({
            **manifest,
            "status": "due_for_review" if overdue else "current",
            "reason": (f"Past its review date ({manifest['review_by']}). Ask its maintainer,"
                       f" {manifest['maintainer']}, to review it; until then no new"
                       " document can be started from it.") if overdue else "",
            "template_specs": {t: catalog["templates"][t] for t in manifest["templates"]},
        })
    return packs


class PackService:
    """Documents started from packs. Revisions go through BriefService, the one
    writer for artifacts and revisions."""

    def __init__(self, ws: ManagerWorkspace):
        self.ws = ws
        self.briefs = BriefService(ws)

    def start(self, pack_id: str, template_id: str, *, project_id: str | None = None,
              today: str | None = None) -> str:
        """Start a draft from one template of a current pack. Returns the document id."""
        today = today or self.ws.local_today()
        pack = next((p for p in available_packs(today) if p["id"] == pack_id), None)
        if pack is None:
            raise PackError(f"there is no pack called {pack_id}")
        if pack["status"] != "current":
            raise PackError(pack["reason"])
        if template_id not in pack["templates"]:
            raise PackError(f"the {pack['title']} has no template {template_id}")
        project = self.ws._require_row("projects", project_id or None)
        spec = pack["template_specs"][template_id]
        title = spec["title"] + (f" — {project['title']}" if project else "")
        body = compose_document(pack, template_id, spec, project)
        refs = [project["id"]] if project else []
        with self.ws.store.transaction() as db:
            artifact_id = new_id("art")
            db.execute(
                "INSERT INTO artifacts (id, workspace_id, project_id, kind, title, created_at)"
                " VALUES (?, ?, ?, 'pack_document', ?, ?)",
                (artifact_id, self.ws.info.id, project["id"] if project else None, title,
                 self.ws.clock()),
            )
            db.execute(
                "INSERT INTO pack_documents (artifact_id, workspace_id, pack_id, pack_version,"
                " template_id, template_sha256) VALUES (?, ?, ?, ?, ?, ?)",
                (artifact_id, self.ws.info.id, pack_id, pack["version"], template_id,
                 pack["templates"][template_id]),
            )
            self.ws.store.log(self.ws.info.owner, "create", "artifact", artifact_id)
            self.briefs._add_revision(artifact_id, body, refs, self.ws.info.owner)
        return artifact_id

    def save(self, document_id: str, body: str, base_sha256: str) -> Revision:
        """The manager's edit, as a new draft. Refused if the text changed since
        they opened it, so an edit never silently replaces another."""
        self._document(document_id)
        body = body.replace("\r\n", "\n")
        if not body.strip():
            raise PackError("a document needs content")
        if len(body) > MAX_DOCUMENT_CHARS:
            raise PackError(f"keep a document under {MAX_DOCUMENT_CHARS} characters")
        with self.ws.store.transaction():
            latest = self.briefs.latest(document_id)
            if latest is None or latest.body_sha256 != base_sha256:
                raise StaleRevision("this document changed since you opened it; open it again")
            if latest.body_markdown == body:
                raise PackError("nothing changed; edit the text before saving")
            return self.briefs.revise(document_id, body, self.ws.info.owner)

    def view(self, document_id: str) -> dict[str, Any]:
        document = self._document(document_id)
        latest = self.briefs.latest(document_id)
        accepted = self.briefs.accepted(document_id)
        return {
            "sample": self.ws.info.sample,
            "document": document,
            "current": {
                "revision": self.briefs.as_dict(latest),
                "markdown": self.briefs.render(latest, draft_banner=PACK_DRAFT_BANNER),
                "body_markdown": latest.body_markdown,
            },
            "accepted": self.briefs.as_dict(accepted) if accepted else None,
        }

    def documents(self) -> list[dict[str, Any]]:
        return [document_dict(row) for row in self.ws.store.conn.execute(
            _DOCUMENTS + " WHERE a.workspace_id = ? ORDER BY latest.created_at DESC, a.id",
            (self.ws.info.id,))]

    def _document(self, document_id: str) -> dict[str, Any]:
        row = self.ws.store.conn.execute(
            _DOCUMENTS + " WHERE a.workspace_id = ? AND a.id = ?",
            (self.ws.info.id, document_id)).fetchone()
        if row is None:
            raise PackError("this document is not in this workspace")
        return document_dict(row)


_DOCUMENTS = (
    "SELECT a.id, a.title, a.project_id, p.title AS project_title, d.pack_id,"
    " d.pack_version, d.template_id, latest.revision_no, latest.status,"
    " latest.created_at AS updated_at,"
    " (SELECT count(*) FROM artifact_revisions r WHERE r.artifact_id = a.id"
    "  AND r.status = 'accepted') AS has_accepted"
    " FROM artifacts a JOIN pack_documents d ON d.artifact_id = a.id"
    " LEFT JOIN projects p ON p.id = a.project_id"
    " JOIN artifact_revisions latest ON latest.artifact_id = a.id AND latest.revision_no ="
    "  (SELECT max(revision_no) FROM artifact_revisions WHERE artifact_id = a.id)"
)


def document_dict(row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "project_id": row["project_id"],
        "project_title": row["project_title"],
        "pack_id": row["pack_id"],
        "pack_version": row["pack_version"],
        "template_id": row["template_id"],
        "revision_no": row["revision_no"],
        "status": row["status"],
        "has_accepted": bool(row["has_accepted"]),
        "updated_at": row["updated_at"],
    }


def compose_document(pack: dict[str, Any], template_id: str, spec: dict[str, Any],
                     project) -> str:
    """The first draft: the template's headings and guidance, the pack's
    rules, and where it came from. Nothing is written for the manager."""
    title = spec["title"] + (f" — {project['title']}" if project else "")
    lines = [f"# {title}", "",
             f"**Pack:** {pack['title']} {pack['version']} (template `{template_id}`),"
             f" maintained by {pack['maintainer']}; reviewed {pack['reviewed_on']},"
             f" next review by {pack['review_by']}.", ""]
    if project:
        lines += [f"**Project:** {project['title']} `{project['id']}`", ""]
    lines += ["## Before you use this", ""]
    lines += [f"- {rule}" for rule in pack["rules"]]
    lines.append("")
    for section in spec["sections"]:
        lines += [f"## {section['heading']}", "", f"> {section['guidance']}", "",
                  "_Write this section._", ""]
    return "\n".join(lines)


__all__ = ["PACK_DRAFT_BANNER", "PackError", "PackService", "available_packs", "load_pack",
           "template_sha256"]
