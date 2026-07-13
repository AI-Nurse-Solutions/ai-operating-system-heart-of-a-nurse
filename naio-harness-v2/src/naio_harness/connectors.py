from __future__ import annotations

import ipaddress
import json
from pathlib import Path
from urllib.parse import urlparse


class ConnectorError(RuntimeError):
    pass


class ConnectorPolicy:
    def __init__(self, path: Path):
        self.policy = json.loads(path.read_text(encoding="utf-8"))

    def validate(self, manifest: dict) -> dict[str, str | bool]:
        required = {"connector_id", "endpoint", "auth_mode", "token_passthrough", "data_class", "capabilities"}
        if set(manifest) != required:
            raise ConnectorError("connector manifest fields are missing or unknown")
        if manifest["token_passthrough"] or self.policy["token_passthrough"]:
            raise ConnectorError("token passthrough is forbidden")
        parsed = urlparse(manifest["endpoint"])
        if self.policy["require_https"] and parsed.scheme != "https":
            raise ConnectorError("connector endpoint must use HTTPS")
        host = (parsed.hostname or "").lower()
        if not host:
            raise ConnectorError("connector endpoint has no host")
        if host not in set(self.policy["allowed_hosts"]):
            raise ConnectorError("connector host is not allowlisted")
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            address = None
        if address is not None:
            if address.is_loopback and not self.policy["allow_loopback"]:
                raise ConnectorError("loopback connector denied")
            if address.is_private and not self.policy["allow_private_networks"]:
                raise ConnectorError("private-network connector denied")
        if manifest["data_class"] != "public":
            raise ConnectorError("canary connectors are public-data-only")
        if not manifest["capabilities"]:
            raise ConnectorError("connector must declare capabilities")
        return {"allowed": True, "connector_id": manifest["connector_id"], "host": host, "data_class": "public"}
