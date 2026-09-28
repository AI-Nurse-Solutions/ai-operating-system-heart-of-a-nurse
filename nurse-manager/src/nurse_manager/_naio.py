"""Bridge to the existing Integration Contract in ``naio-integrations``.

The manager core reuses — never copies — the privacy screen, the EDENA
policy engine, and the synthetic-content banner. Inside this repository the
package is resolved from its source tree; a packaged build installs it
alongside this package and the path insertion becomes a no-op.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[3] / "naio-integrations" / "src"

try:  # pragma: no cover - depends on how the app was installed
    import naio_integrations  # noqa: F401
except ImportError:  # pragma: no cover
    if _SRC.is_dir() and str(_SRC) not in sys.path:
        sys.path.insert(0, str(_SRC))

from naio_integrations.contract import (  # noqa: E402
    ActionMode,
    Actor,
    DataClass,
    DataZone,
    Decision,
    GatewayRequest,
    PolicyDecision,
    RiskTier,
)
from naio_integrations.deliverables import SYNTHETIC_BANNER  # noqa: E402
from naio_integrations.policy import EdenaPolicyEngine  # noqa: E402
from naio_integrations.privacy import PrivacyScreen  # noqa: E402

from . import resources  # noqa: E402


def privacy_screen() -> PrivacyScreen:
    """The privacy screen, configured from wherever the recognizers live."""
    return PrivacyScreen(resources.naio_config("privacy-recognizers.json"))


def edena_engine() -> EdenaPolicyEngine:
    """The authoritative EDENA engine, configured from wherever its policy lives."""
    return EdenaPolicyEngine(resources.naio_config("edena-gateway-policy.json"))


__all__ = [
    "ActionMode",
    "Actor",
    "DataClass",
    "DataZone",
    "Decision",
    "EdenaPolicyEngine",
    "GatewayRequest",
    "PolicyDecision",
    "PrivacyScreen",
    "RiskTier",
    "SYNTHETIC_BANNER",
    "edena_engine",
    "privacy_screen",
]
