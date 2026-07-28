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
  the EDENA policy actor from the *active role and workspace*, and an
  authenticated organization must BE the current workspace: an org
  login carried into a personal or foreign workspace grants nothing.
* Cross-role suggestions are optional and always explain why they are
  relevant.

Persistence is transactional: every mutation acquires an exclusive file
lock (cross-platform, stdlib-only — see ``locking``), reloads the
latest state from disk, applies and validates the change, and writes
atomically through a per-writer temporary file — so concurrent
instances on the same state file serialize instead of losing updates.
Reads serve the instance's snapshot; mutations always apply to the
freshest state. Free-text quick capture (inbox, calendar, portfolio)
passes through the privacy screen before it is persisted, so
identifiers never land in plaintext identity state. Roles are validated
against the Mission Control packet catalog — the same configuration
that defines the role packets.
"""

from __future__ import annotations

import json
import os
import secrets
from pathlib import Path
from typing import Any, Callable

from . import locking
from .contract import Actor
from .packets import PacketCatalog
from .privacy import PrivacyScreen

STATE_VERSION = "1.0.0"


class IdentityError(ValueError):
    pass


def _fresh_state(identity_id: str) -> dict[str, Any]:
    return {
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


class MultiRoleIdentity:
    """A single identity holding one or more Mission Control role lenses."""

    def __init__(
        self,
        identity_id: str,
        state_path: Path,
        catalog: PacketCatalog | None = None,
        privacy: PrivacyScreen | None = None,
    ):
        if not identity_id.strip():
            raise IdentityError("an identity requires a non-empty id")
        self.identity_id = identity_id
        self.catalog = catalog or PacketCatalog()
        self.privacy = privacy or PrivacyScreen()
        self.state_path = state_path
        self._lock_path = state_path.with_name(state_path.name + ".lock")
        if state_path.exists():
            self.state = self._load()
        else:
            self.state = _fresh_state(identity_id)
            self._mutate(lambda state: None)

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

        def apply(state: dict[str, Any]) -> None:
            if role in state["roles"]:
                return
            state["roles"].append(role)
            if state["active_role"] is None:
                state["active_role"] = role

        self._mutate(apply)

    def deactivate_role(self, role: str) -> None:
        def apply(state: dict[str, Any]) -> None:
            if role not in state["roles"]:
                raise IdentityError(f"role is not activated: {role}")
            if len(state["roles"]) == 1:
                raise IdentityError("an identity must keep at least one active role")
            state["roles"].remove(role)
            if state["active_role"] == role:
                state["active_role"] = state["roles"][0]

        self._mutate(apply)

    def switch_role(self, role: str) -> str:
        def apply(state: dict[str, Any]) -> str:
            if role not in state["roles"]:
                raise IdentityError(
                    f"cannot switch to a role that is not activated: {role}"
                )
            state["active_role"] = role
            return role

        return self._mutate(apply)

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
        def apply(state: dict[str, Any]) -> None:
            if role not in state["roles"]:
                raise IdentityError(f"role is not activated: {role}")
            state["layouts"][role] = {**layout, "remembered": True}

        self._mutate(apply)

    # ------------------------------------------------------------------
    # Shared stores — held once, filtered by lens, never copied.

    def add_project(self, project_id: str, title: str, roles: tuple[str, ...]) -> None:
        def apply(state: dict[str, Any]) -> None:
            if not roles:
                raise IdentityError("a project must be tagged to at least one role")
            for role in roles:
                if role not in state["roles"]:
                    raise IdentityError(
                        f"cannot tag project to inactive role: {role}"
                    )
            state["projects"][project_id] = {
                "title": title,
                "roles": sorted(set(roles)),
            }

        self._mutate(apply)

    def add_competency(self, competency_id: str, name: str) -> None:
        def apply(state: dict[str, Any]) -> None:
            state["competencies"][competency_id] = {"name": name, "applications": {}}

        self._mutate(apply)

    def set_competency_application(
        self, competency_id: str, role: str, application: str
    ) -> None:
        def apply(state: dict[str, Any]) -> None:
            competency = state["competencies"].get(competency_id)
            if competency is None:
                raise IdentityError(f"unknown competency: {competency_id}")
            if role not in state["roles"]:
                raise IdentityError(f"role is not activated: {role}")
            competency["applications"][role] = application

        self._mutate(apply)

    def add_inbox_item(self, item: str) -> None:
        screened = self._screen(item)
        self._mutate(lambda state: state["inbox"].append(screened))

    def add_calendar_entry(self, entry: str) -> None:
        screened = self._screen(entry)
        self._mutate(lambda state: state["calendar"].append(screened))

    def add_portfolio_item(self, item: str) -> None:
        screened = self._screen(item)
        self._mutate(lambda state: state["portfolio"].append(screened))

    def _screen(self, text: str) -> str:
        """Quick capture crosses a storage boundary — screen it first."""
        return self.privacy.transform(str(text)).transformed_text

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
        if authenticated_org and authenticated_org != workspace_tenant:
            raise IdentityError(
                "authenticated organization must match the current workspace;"
                " an org login grants nothing in a personal or foreign workspace"
            )
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
        def apply(state: dict[str, Any]) -> None:
            state["cross_role_suggestions_enabled"] = bool(enabled)

        self._mutate(apply)

    def suggestions(self) -> tuple[dict[str, str], ...]:
        if not self.state["cross_role_suggestions_enabled"]:
            return ()
        active = self.state["active_role"]
        activated = set(self.state["roles"])
        results = []
        for project_id, project in sorted(self.state["projects"].items()):
            # Stale tags from since-deactivated roles never surface.
            other_roles = [
                r for r in project["roles"] if r != active and r in activated
            ]
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
    # Transactional persistence: lock -> reload -> mutate -> atomic write.

    def _load(self) -> dict[str, Any]:
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        if state.get("identity_id") != self.identity_id:
            raise IdentityError(
                "state file belongs to a different identity; refusing to load"
            )
        return state

    def _mutate(self, apply: Callable[[dict[str, Any]], Any]) -> Any:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock_path.open("a+", encoding="utf-8") as lock:
            locking.acquire(lock)
            try:
                if self.state_path.exists():
                    self.state = self._load()
                result = apply(self.state)
                tmp = self.state_path.with_name(
                    f".{self.state_path.name}.{os.getpid()}"
                    f".{secrets.token_hex(4)}.tmp"
                )
                tmp.write_text(
                    json.dumps(self.state, indent=2, sort_keys=True),
                    encoding="utf-8",
                )
                tmp.replace(self.state_path)
                return result
            finally:
                locking.release(lock)
