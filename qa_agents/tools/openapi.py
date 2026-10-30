"""OpenAPI parsing: endpoints, request fields, constraints and documentation gaps.

Supports Swagger 2.0, OpenAPI 3.0 and 3.1 (type arrays, `nullable`, allOf composition), local
`$ref`s at any depth (with cycle protection), and reports external `$ref`s it cannot follow.
"""

from __future__ import annotations

import re
from typing import Any

import yaml

from qa_agents.core.llm import AgentError

HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")
CONSTRAINT_KEYS = (
    "minLength", "maxLength", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
    "pattern", "enum", "const", "format", "minItems", "maxItems", "uniqueItems",
)


def load_spec(text: str) -> dict[str, Any]:
    try:
        spec = yaml.safe_load(text)  # JSON is valid YAML
    except yaml.YAMLError as exc:
        raise AgentError(f"The spec is not valid YAML/JSON: {exc}") from exc
    if not isinstance(spec, dict) or not ("openapi" in spec or "swagger" in spec):
        raise AgentError("Not an OpenAPI document: expected an 'openapi' or 'swagger' field at the top level.")
    if not isinstance(spec.get("paths"), dict) or not spec["paths"]:
        raise AgentError("The spec has no 'paths', so there is nothing to test.")
    return spec


class _Resolver:
    def __init__(self, spec: dict):
        self.spec = spec
        self.external: set[str] = set()

    def resolve(self, node: Any, seen: frozenset = frozenset()) -> Any:
        while isinstance(node, dict) and "$ref" in node:
            ref = node["$ref"]
            if not ref.startswith("#/"):
                self.external.add(ref)
                return {}
            if ref in seen:
                return {}  # circular reference
            seen = seen | {ref}
            target: Any = self.spec
            for part in ref[2:].split("/"):
                part = part.replace("~1", "/").replace("~0", "~")
                target = target.get(part) if isinstance(target, dict) else None
                if target is None:
                    self.external.add(f"{ref} (target not found)")
                    return {}
            node = target
        if isinstance(node, dict) and "allOf" in node:
            merged: dict[str, Any] = {k: v for k, v in node.items() if k != "allOf"}
            for part in node["allOf"]:
                part = self.resolve(part, seen)
                if isinstance(part, dict):
                    merged.setdefault("properties", {}).update(part.get("properties", {}))
                    merged["required"] = list(merged.get("required", [])) + list(part.get("required", []))
                    for k, v in part.items():
                        if k not in ("properties", "required"):
                            merged.setdefault(k, v)
            return merged
        return node


def _type_of(schema: dict) -> tuple[str, bool]:
    t = schema.get("type")
    nullable = bool(schema.get("nullable"))
    if isinstance(t, list):  # OpenAPI 3.1
        nullable = nullable or "null" in t
        t = next((x for x in t if x != "null"), "untyped")
    if not t:
        if "properties" in schema:
            t = "object"
        elif "items" in schema:
            t = "array"
        elif any(k in schema for k in ("oneOf", "anyOf")):
            t = "oneOf/anyOf"
        else:
            t = "untyped"
    return t, nullable


def _fields(r: _Resolver, schema: Any, prefix: str = "", depth: int = 0) -> list[dict[str, Any]]:
    schema = r.resolve(schema)
    if not isinstance(schema, dict) or depth > 5:
        return []
    out = []
    required = set(schema.get("required", []))
    for name, prop in (schema.get("properties") or {}).items():
        prop = r.resolve(prop)
        if not isinstance(prop, dict):
            continue
        path = f"{prefix}{name}"
        ftype, nullable = _type_of(prop)
        out.append(
            {
                "field": path,
                "type": ftype,
                "required": name in required,
                "nullable": nullable,
                "read_only": bool(prop.get("readOnly")),
                "constraints": {k: prop[k] for k in CONSTRAINT_KEYS if k in prop},
            }
        )
        if ftype == "object":
            out += _fields(r, prop, path + ".", depth + 1)
        elif ftype == "array":
            out += _fields(r, prop.get("items", {}), path + "[].", depth + 1)
    return out


def _request_schema(r: _Resolver, op: dict, params: list[dict], swagger2: bool) -> Any:
    if swagger2:
        body = next((p for p in params if p.get("in") == "body"), None)
        return body.get("schema") if body else None
    content = (r.resolve(op.get("requestBody") or {}).get("content") or {})
    media = next((v for k, v in content.items() if "json" in k), None) or next(iter(content.values()), None)
    return (media or {}).get("schema")


def _response_has_body(resp: dict, swagger2: bool) -> bool:
    return bool(resp.get("schema")) if swagger2 else bool(resp.get("content"))


def analyse_spec(spec: dict[str, Any]) -> dict[str, Any]:
    r = _Resolver(spec)
    swagger2 = "swagger" in spec
    global_security = spec.get("security")
    schemes = spec.get("securityDefinitions") if swagger2 else (spec.get("components") or {}).get("securitySchemes")
    endpoints, operation_ids = [], {}
    for path, item in spec["paths"].items():
        item = r.resolve(item) or {}
        template_params = set(re.findall(r"{([^}]+)}", path))
        for method in HTTP_METHODS:
            op = item.get(method)
            if not isinstance(op, dict):
                continue
            params = [r.resolve(p) for p in item.get("parameters", []) + op.get("parameters", [])]
            params = [p for p in params if isinstance(p, dict)]
            body = _request_schema(r, op, params, swagger2)
            fields = _fields(r, body) if body else []
            responses = {str(code): r.resolve(resp) or {} for code, resp in (op.get("responses") or {}).items()}
            endpoint = f"{method.upper()} {path}"
            gaps = []

            if not op.get("operationId"):
                gaps.append("no operationId")
            else:
                operation_ids.setdefault(op["operationId"], []).append(endpoint)
            if not any(c.startswith("2") for c in responses):
                gaps.append("no 2xx response documented")
            if not any(c.startswith("4") for c in responses) and "default" not in responses:
                gaps.append("no 4xx response documented")
            for code, resp in responses.items():
                if code.startswith("2") and code not in ("204", "202") and method != "head" and not _response_has_body(resp, swagger2):
                    gaps.append(f"{code} response has no schema")
            security = op.get("security", global_security)
            if security is None:
                gaps.append("no security requirement declared")
            elif security == [] and global_security:
                gaps.append("explicitly public (security: []): confirm this is intended")
            elif security and "401" not in responses:
                gaps.append("secured but 401 not documented")
            declared = {p.get("name") for p in params if p.get("in") == "path"}
            for missing in sorted(template_params - declared):
                gaps.append(f"path parameter '{missing}' is not declared")
            if body is not None and "400" not in responses and "422" not in responses:
                gaps.append("accepts a body but documents no 400/422 validation error")
            for f in fields:
                c = f["constraints"]
                if f["type"] == "untyped":
                    gaps.append(f"field '{f['field']}' has no type")
                elif f["type"] == "string" and not ({"maxLength", "enum", "format", "pattern", "const"} & c.keys()):
                    gaps.append(f"string field '{f['field']}' has no maxLength, format, pattern or enum")
                elif f["type"] in ("integer", "number") and not ({"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "enum"} & c.keys()):
                    gaps.append(f"numeric field '{f['field']}' has no minimum/maximum")
                elif f["type"] == "array" and "maxItems" not in c:
                    gaps.append(f"array field '{f['field']}' has no maxItems")
            for p in params:
                if p.get("in") in ("query", "header", "path"):
                    ps = r.resolve(p.get("schema", p))  # Swagger 2 puts type on the parameter itself
                    ptype, _ = _type_of(ps if isinstance(ps, dict) else {})
                    if ptype == "string" and not ({"maxLength", "enum", "format", "pattern"} & set(ps)):
                        gaps.append(f"{p['in']} parameter '{p.get('name')}' has no format, pattern or maxLength")
            endpoints.append(
                {
                    "endpoint": endpoint,
                    "summary": op.get("summary") or (op.get("description") or "")[:120],
                    "deprecated": bool(op.get("deprecated")),
                    "secured": bool(security),
                    "parameters": [f"{p.get('in')}:{p.get('name')}{'*' if p.get('required') else ''}" for p in params if p.get("in") != "body"],
                    "request_fields": fields,
                    "documented_responses": sorted(responses),
                    "gaps": gaps,
                }
            )

    spec_gaps = []
    for op_id, eps in operation_ids.items():
        if len(eps) > 1:
            spec_gaps.append(f"operationId '{op_id}' is used by {', '.join(eps)}")
    if not schemes:
        spec_gaps.append("no security schemes defined")
    if not swagger2 and not spec.get("servers"):
        spec_gaps.append("no servers defined")
    if r.external:
        spec_gaps.append("unresolved references (not analysed): " + ", ".join(sorted(r.external)[:10]))
    info = spec.get("info") or {}
    return {
        "title": info.get("title", ""),
        "version": info.get("version", ""),
        "spec_format": f"Swagger {spec['swagger']}" if swagger2 else f"OpenAPI {spec.get('openapi')}",
        "endpoint_count": len(endpoints),
        "endpoints_with_gaps": sum(1 for e in endpoints if e["gaps"]),
        "spec_level_gaps": spec_gaps,
        "endpoints": endpoints,
    }
