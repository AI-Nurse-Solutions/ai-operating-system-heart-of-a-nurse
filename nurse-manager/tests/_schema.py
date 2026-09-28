"""Minimal JSON Schema validator for the constructs the contracts use.

Stdlib only, so every CI leg (and a clean machine) can check contracts
offline. Supported: $ref (local #/$defs), anyOf, enum, const, type
(including type lists; booleans are never integers), pattern, minimum,
maximum, minItems, maxItems, items, properties, required,
additionalProperties=false, and format date-time. The Node test checks
the same fixtures with ajv in strict draft 2020-12 mode, so a construct
this validator ignores cannot hide a contract break.
"""

import re
from datetime import datetime

_TYPES = {
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "array": lambda v: isinstance(v, list),
    "object": lambda v: isinstance(v, dict),
    "null": lambda v: v is None,
}


def check(value, schema, root, path="$"):
    """Return "" when ``value`` satisfies ``schema``, else the first error."""
    if schema is True or schema == {}:
        return ""
    if "$ref" in schema:
        return check(value, root["$defs"][schema["$ref"].split("/")[-1]], root, path)
    if "anyOf" in schema:
        errors = [check(value, option, root, path) for option in schema["anyOf"]]
        return "" if not all(errors) else f"{path}: matches no anyOf option ({errors})"
    if "const" in schema and (value != schema["const"] or type(value) is not type(schema["const"])):
        return f"{path}: expected {schema['const']!r}, got {value!r}"
    if "enum" in schema and value not in schema["enum"]:
        return f"{path}: {value!r} not in {schema['enum']}"
    kinds = schema.get("type")
    if kinds is not None:
        kinds = kinds if isinstance(kinds, list) else [kinds]
        if not any(_TYPES[k](value) for k in kinds):
            return f"{path}: expected {'/'.join(kinds)}, got {type(value).__name__}"
    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            return f"{path}: {value!r} does not match {schema['pattern']}"
        if schema.get("format") == "date-time":
            try:
                datetime.fromisoformat(value)
            except ValueError:
                return f"{path}: not a date-time"
    if _TYPES["number"](value):
        if "minimum" in schema and value < schema["minimum"]:
            return f"{path}: {value} < {schema['minimum']}"
        if "maximum" in schema and value > schema["maximum"]:
            return f"{path}: {value} > {schema['maximum']}"
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            return f"{path}: fewer than {schema['minItems']} items"
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            return f"{path}: more than {schema['maxItems']} items"
        for i, item in enumerate(value):
            err = check(item, schema.get("items", {}), root, f"{path}[{i}]")
            if err:
                return err
    if isinstance(value, dict):
        props = schema.get("properties", {})
        missing = [k for k in schema.get("required", []) if k not in value]
        if missing:
            return f"{path}: missing {missing}"
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(props))
            if extra:
                return f"{path}: unexpected {extra}"
        for key, sub in props.items():
            if key in value:
                err = check(value[key], sub, root, f"{path}.{key}")
                if err:
                    return err
    return ""
