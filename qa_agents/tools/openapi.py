"""OpenAPI 3 parsing: endpoints, request fields, constraints and documentation gaps."""

from __future__ import annotations

from typing import Any

import yaml

HTTP_METHODS = ("get", "post", "put", "patch", "delete")
CONSTRAINT_KEYS = ("minLength", "maxLength", "minimum", "maximum", "pattern", "enum", "format", "minItems", "maxItems")


def load_spec(text: str) -> dict[str, Any]:
    spec = yaml.safe_load(text)  # JSON is valid YAML
    if not isinstance(spec, dict) or "paths" not in spec:
        raise ValueError("Not an OpenAPI document: no 'paths' section found.")
    return spec


def _resolve(spec: dict, node: Any, depth: int = 0) -> Any:
    if isinstance(node, dict) and "$ref" in node and depth < 8:
        target: Any = spec
        for part in node["$ref"].lstrip("#/").split("/"):
            target = target.get(part, {}) if isinstance(target, dict) else {}
        return _resolve(spec, target, depth + 1)
    return node


def _fields(spec: dict, schema: Any, prefix: str = "", depth: int = 0) -> list[dict[str, Any]]:
    schema = _resolve(spec, schema)
    if not isinstance(schema, dict) or depth > 4:
        return []
    out = []
    required = set(schema.get("required", []))
    for name, prop in (schema.get("properties") or {}).items():
        prop = _resolve(spec, prop)
        path = f"{prefix}{name}"
        constraints = {k: prop[k] for k in CONSTRAINT_KEYS if k in prop}
        out.append(
            {
                "field": path,
                "type": prop.get("type", "untyped"),
                "required": name in required,
                "constraints": constraints,
            }
        )
        if prop.get("type") == "object" or "properties" in prop:
            out += _fields(spec, prop, path + ".", depth + 1)
        elif prop.get("type") == "array":
            out += _fields(spec, prop.get("items", {}), path + "[].", depth + 1)
    return out


def analyse_spec(spec: dict[str, Any]) -> dict[str, Any]:
    endpoints = []
    global_security = bool(spec.get("security"))
    for path, item in spec["paths"].items():
        for method in HTTP_METHODS:
            op = item.get(method)
            if not op:
                continue
            op = _resolve(spec, op)
            body = (((op.get("requestBody") or {}).get("content") or {}).get("application/json") or {}).get("schema")
            fields = _fields(spec, body) if body else []
            params = [_resolve(spec, p) for p in item.get("parameters", []) + op.get("parameters", [])]
            responses = {str(code): _resolve(spec, r) for code, r in (op.get("responses") or {}).items()}
            gaps = []
            if not any(c.startswith("4") for c in responses):
                gaps.append("no 4xx response documented")
            for code, resp in responses.items():
                if code.startswith("2") and code != "204" and not (resp or {}).get("content"):
                    gaps.append(f"{code} response has no schema")
            if not (global_security or op.get("security")):
                gaps.append("no security requirement declared")
            for f in fields:
                if f["type"] == "untyped":
                    gaps.append(f"field '{f['field']}' has no type")
                elif f["type"] == "string" and not f["constraints"]:
                    gaps.append(f"string field '{f['field']}' has no length, format or pattern")
                elif f["type"] in ("integer", "number") and not {"minimum", "maximum"} & f["constraints"].keys():
                    gaps.append(f"numeric field '{f['field']}' has no minimum/maximum")
            endpoints.append(
                {
                    "endpoint": f"{method.upper()} {path}",
                    "summary": op.get("summary", ""),
                    "path_and_query_params": [p.get("name", "") for p in params],
                    "request_fields": fields,
                    "documented_responses": sorted(responses),
                    "gaps": gaps,
                }
            )
    return {
        "title": (spec.get("info") or {}).get("title", ""),
        "version": (spec.get("info") or {}).get("version", ""),
        "endpoint_count": len(endpoints),
        "endpoints": endpoints,
    }
