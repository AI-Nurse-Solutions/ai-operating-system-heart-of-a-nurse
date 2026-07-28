"""Multi-role identity (Mission Control spec section 9).

One professional, one identity, several role lenses — never separate
accounts or disconnected installations. The rules this module makes
structural:

* Shared content is held once. The inbox, calendar, portfolio, projects,
  and competencies are single stores; a role lens filters them, it never
  copies them.
* Projects can be tagged to one or several roles and appear in each
  tagged lens without duplication.
* Shared competencies appear once, with role-specific applications.
* The dashboard remembers the last layout for each role; switching roles
  preserves shared content and per-role layouts.
* Permissions depend on the current workspace, data class, institution,
  and task — never merely on professional title. ``actor_for`` builds
  the EDENA policy actor from the *active role and workspace*, so a
  leader hat grants nothing outside an authenticated context.
* Cross-role suggestions are optional and always explain why they are
  relevant.

State is durable JSON with atomic writes, so a role switch survives any
interruption. Roles are validated against the Mission Control packet
catalog — the same configuration that defines the role packets.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contract import Actor
from .packets import PacketCatalog

STATE_VERSION = "1.0.0"


class IdentityError(ValueError):
    pass


class MultiRoleIdentity:
    """A single identity holding one or more Mission Control role lenses."""

    def __init__(
        self,
        identity_id: str,
        state_path: Path,
        catalog: PacketCatalog | None = None,
    ):
        if not identity_id.strip():
            raise IdentityError("an identity requires a non-empty id")
        self.catalog = catalog or PacketCatalog()
        self.state_path = state_path
        if state_path.exists():
            self.state = json.loads(state_path.read_text(encoding="utf-8"))
            if self.state.get("identity_id") != identity_id:
                raise IdentityError(
                    "state file belongs to a different identity; refusing to load"
                )
        else:
            self.state = {
                "state_version": STATE_VERSION,
                "identity_id": identity_id,
                "roles": [],
                "active_role": None,
                "layouts": {},
                "projects": {},
                "competencies": {},
                "inbox": [],
                "calendar": [],
                "portfolio": [],
                "cross_role_suggestions_enabled": False,
            }
            self._save()

    # ------------------------------------------------------------------
    # Roles

    def roles(self) -> tuple[str, ...]:
        return tuple(self.state["roles"])

    @property
    def active_role(self) -> str | None:
        return self.state["active_role"]

    def activate_role(self, role: str) -> None:
        if role not in self.catalog.roles():
            raise IdentityError(f"unknown role: {role}")
        if role in self.state["roles"]:
            return
        self.state["roles"].append(role)
        if self.state["active_role"] is None:
            self.state["active_role"] = role
        self._save()

    def deactivate_role(self, role: str) -> None:
        if role not in self.state["roles"]:
            raise IdentityError(f"role is not activated: {role}")
        if len(self.state["roles"]) == 1:
            raise IdentityError("an identity must keep at least one active role")
        self.state["roles"].remove(role)
        if self.state["active_role"] == role:
            self.state["active_role"] = self.state["roles"][0]
        self._save()

    def switch_role(self, role: str) -> str:
        if role not in self.state["roles"]:
            raise IdentityError(
                f"cannot switch to a role that is not activated: {role}"
            )
        self.state["active_role"] = role
        self._save()
        return role

    # ------------------------------------------------------------------
    # Layouts — remembered per role; defaults come from the packet catalog.

    def layout_for(self, role: str) -> dict[str, Any]:
        if role not in self.state["roles"]:
            raise IdentityError(f"role is not activated: {role}")
        remembered = self.state["layouts"].get(role)
        if remembered is not None:
            return remembered
        manifest = self.catalog.build_manifest(role)
        return {"home_cards": manifest["role_modules"], "remembered": False}

    def remember_layout(self, role: str, layout: dict[str, Any]) -> None:
        if role not in self.state["roles"]:
            raise IdentityError(f"role is not activated: {role}")
        self.state["layouts"][role] = {**layout, "remembered": True}
        self._save()

    # ------------------------------------------------------------------
    # Shared stores — held once, filtered by lens, never copied.

    def add_project(self, project_id: str, title: str, roles: tuple[str, ...]) -> None:
        if not roles:
            raise IdentityError("a project must be tagged to at least one role")
        for role in roles:
            if role not in self.state["roles"]:
                raise IdentityError(f"cannot tag project to inactive role: {role}")
        self.state["projects"][project_id] = {
            "title": title,
            "roles": sorted(set(roles)),
        }
        self._save()

    def add_competency(self, competency_id: str, name: str) -> None:
        self.state["competencies"][competency_id] = {"name": name, "applications": {}}
        self._save()

    def set_competency_application(
        self, competency_id: str, role: str, application: str
    ) -> None:
        competency = self.state["competencies"].get(competency_id)
        if competency is None:
            raise IdentityError(f"unknown competency: {competency_id}")
        if role not in self.state["roles"]:
            raise IdentityError(f"role is not activated: {role}")
        competency["applications"][role] = application
        self._save()

    def add_inbox_item(self, item: str) -> None:
        self.state["inbox"].append(item)
        self._save()

    def add_calendar_entry(self, entry: str) -> None:
        self.state["calendar"].append(entry)
        self._save()

    def add_portfolio_item(self, item: str) -> None:
        self.state["portfolio"].append(item)
        self._save()

    # ------------------------------------------------------------------
    # Lenses

    def view(self, role: str | None = None) -> dict[str, Any]:
        """The workspace through one role lens. Shared stores are the
        same objects for every lens — a lens filters, it never copies."""
        lens = role or self.state["active_role"]
        if lens is None or lens not in self.state["roles"]:
            raise IdentityError(f"role is not activated: {lens}")
        projects = {
            project_id: project
            for project_id, project in self.state["projects"].items()
            if lens in project["roles"]
        }
        competencies = {
            competency_id: {
                "name": competency["name"],
                "application": competency["applications"].get(lens),
            }
            for competency_id, competency in self.state["competencies"].items()
        }
        return {
            "identity_id": self.state["identity_id"],
            "role": lens,
            "layout": self.layout_for(lens),
            "projects": projects,
            "competencies": competencies,
            "inbox": self.state["inbox"],
            "calendar": self.state["calendar"],
            "portfolio": self.state["portfolio"],
        }

    # ------------------------------------------------------------------
    # Permissions — workspace and task decide, never the title.

    def actor_for(
        self,
        workspace_tenant: str,
        authenticated_org: str | None = None,
        approvals: tuple[str, ...] = (),
    ) -> Actor:
        if self.state["active_role"] is None:
            raise IdentityError("no active role; activate one before acting")
        return Actor(
            actor_id=self.state["identity_id"],
            role=self.state["active_role"],
            tenant=workspace_tenant,
            authenticated_org=authenticated_org,
            approvals=approvals,
        )

    # ------------------------------------------------------------------
    # Cross-role suggestions — optional, always explained.

    def enable_cross_role_suggestions(self, enabled: bool) -> None:
        self.state["cross_role_suggestions_enabled"] = bool(enabled)
        self._save()

    def suggestions(self) -> tuple[dict[str, str], ...]:
        if not self.state["cross_role_suggestions_enabled"]:
            return ()
        active = self.state["active_role"]
        results = []
        for project_id, project in sorted(self.state["projects"].items()):
            other_roles = [r for r in project["roles"] if r != active]
            if active not in project["roles"] and other_roles:
                results.append(
                    {
                        "kind": "project",
                        "reference": project_id,
                        "suggestion": f"Review '{project['title']}' from your"
                        f" {', '.join(other_roles)} lens.",
                        "because": (
                            "This project is tagged to another of your roles;"
                            " cross-role visibility is optional and you can"
                            " turn it off."
                        ),
                    }
                )
        return tuple(results)

    # ------------------------------------------------------------------

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(self.state, indent=2, sort_keys=True), encoding="utf-8"
        )
        tmp.replace(self.state_path)
