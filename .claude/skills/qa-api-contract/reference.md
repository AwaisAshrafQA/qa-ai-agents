<!-- Generated from qa_agents/knowledge/api-contract.md by scripts/sync_skill_references.py. Do not edit here. -->

## Functional validation per field
- Required fields missing, null, empty string, wrong type, extra unknown fields (should be rejected or ignored, never stored).
- Strings: below min / at min / at max / above max length, format (email, uuid, date-time), pattern, unicode, whitespace-only.
- Numbers: below minimum, at boundaries, above maximum, zero, negative, decimals where integers expected, very large values.
- Enums: every allowed value, an unknown value, wrong case. Arrays: empty, minItems/maxItems boundaries, duplicates when uniqueItems.
- Content negotiation: wrong Content-Type -> 415; unsupported Accept -> 406; malformed JSON -> 400.

## Status codes for negative tests (RFC 9110, RFC 6585)
- 400 malformed syntax or invalid parameter · 401 missing/invalid credentials (must send WWW-Authenticate)
- 403 authenticated but not allowed (404 may be used to hide existence) · 404 unknown resource
- 405 wrong method (must send Allow) · 409 state conflict / duplicate · 412 failed If-Match precondition
- 413 payload too large · 415 unsupported media type · 422 well-formed but semantically invalid
- 428 precondition required · 429 too many requests (may send Retry-After)
- Any 5xx on invalid input is a defect. Errors should use one schema, ideally RFC 9457 Problem Details
  (application/problem+json with type, title, status, detail, instance); body `status` must equal the HTTP status.

## Security tests: OWASP API Security Top 10 (2023)
- API1 Broken Object Level Authorization: user B's token on user A's {id} must get 403/404, never 200; try guessed/sequential ids.
- API2 Broken Authentication: no token, malformed, expired, tampered signature, JWT alg=none -> 401; login brute force must be throttled.
- API3 Broken Object Property Level Authorization: send role/isAdmin/price/ownerId in bodies (mass assignment) -> rejected
  or ignored; responses must not expose fields beyond the schema (passwords, internal flags).
- API4 Unrestricted Resource Consumption: huge page sizes, oversized payloads (413), deep nesting, bursts (429); spec needs maxLength/maxItems/maximum.
- API5 Broken Function Level Authorization: admin or other users' write endpoints with a normal token -> 403; try switching methods.
- API6 Unrestricted Access to Sensitive Business Flows: automate purchase/signup/coupon/OTP flows; expect throttling or anti-automation.
- API7 Server Side Request Forgery: URL parameters with 169.254.169.254, localhost, file:// must be rejected.
- API8 Security Misconfiguration: no stack traces in errors, security headers, no wildcard CORS with credentials, no TRACE, HTTPS only.
- API9 Improper Inventory Management: old versions (/v1), debug or undocumented endpoints still reachable.
- API10 Unsafe Consumption of APIs: data from third-party APIs is validated like user input.

## Spec quality (Spectral "oas" ruleset equivalents)
- operation-operationId / operation-operationId-unique; path-params (every {param} declared);
  operation-success-response (a 2xx/3xx exists); typed-enum; array-items; oas3-operation-security-defined;
  oas3-valid-schema-example / oas3-valid-media-example (examples must validate against their schema);
  oas3-unused-component; oas3-api-servers; info-description / info-contact.
- Every secured operation documents 401 (and 403 where roles apply); every operation with a body documents 400/422.
- Bounded inputs (maxLength, maxItems, maximum) are also a security control (API4).

## Contract testing
- Provider-side: validate every response against the OpenAPI schema (status, required fields, types, no undocumented fields when the schema says additionalProperties: false).
- Consumer-driven (Pact): consumers publish expectations; the provider verifies them with provider states. Extra response fields are fine.
- Breaking changes (oasdiff): removing an endpoint/response field, adding a required request field or parameter, changing a type,
  removing a request enum value or adding a response enum value. Narrowing requests or widening responses breaks clients.

Sources: OWASP API Security Top 10 2023 https://api-security.owasp.org/editions/2023/en/0x11-t10 · RFC 9110
https://www.rfc-editor.org/rfc/rfc9110.html · RFC 6585 https://www.rfc-editor.org/rfc/rfc6585.html · RFC 9457
https://www.rfc-editor.org/rfc/rfc9457.html · Spectral OpenAPI rules
https://github.com/stoplightio/spectral/blob/develop/docs/reference/openapi-rules.md · Pact
https://docs.pact.io/getting_started/how_pact_works · oasdiff breaking changes https://www.oasdiff.com/docs/breaking-changes
