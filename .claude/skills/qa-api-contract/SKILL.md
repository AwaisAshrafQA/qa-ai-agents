---
name: qa-api-contract
description: Analyse an OpenAPI or Swagger spec and propose request validations, negative tests with expected status codes, response schema checks and gaps in the contract. Use when the user shares an API spec or asks how to test an API or its contract.
---

# API Contract Review

## 1. Get the facts

Find the spec (`openapi.yaml`, `swagger.json`, often under `docs/` or `api/`), then run:

```bash
qa-agents facts api-contract <openapi.yaml>
```

If `qa-agents` is missing, install it: `pip install git+https://github.com/AwaisAshrafQA/qa-ai-agents`.

`facts.endpoints` lists every endpoint with its request fields, constraints, documented responses and `gaps` (missing auth, missing 4xx responses, unbounded strings or numbers). These come from code: cover every gap.

## 2. Analyse

Follow `instructions`. Do not invent endpoints that are not in the spec. If the API's implementation is in this repository, check the gaps against the code.

## 3. Report

Tables for request validations, negative tests (endpoint, request change, expected status, expected error), schema checks and spec gaps (with risk and recommendation).

## 4. Offer next steps

- Write the negative and contract tests in the project's API test framework (REST Assured, Playwright API, pytest with requests, Postman), then run them.
- Draft a patch to the spec that closes the gaps.
