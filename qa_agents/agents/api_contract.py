"""3. API Contract Agent: request validations, negative tests and schema checks from an OpenAPI spec."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from qa_agents.core.base import Agent, facts_block, file_block
from qa_agents.core.llm import AgentError
from qa_agents.tools.openapi import analyse_spec, load_spec


class ValidationCheck(BaseModel):
    endpoint: str
    field: str
    rule: str
    why: str


class NegativeTest(BaseModel):
    endpoint: str
    title: str
    request_change: str
    expected_status: int
    expected_error: str


class SchemaCheck(BaseModel):
    endpoint: str
    status: int
    assertion: str


class SpecGap(BaseModel):
    endpoint: str
    gap: str
    risk: Literal["high", "medium", "low"]
    recommendation: str


class ApiContractReview(BaseModel):
    summary: str
    request_validations: list[ValidationCheck]
    negative_tests: list[NegativeTest]
    schema_checks: list[SchemaCheck]
    spec_gaps: list[SpecGap]


class ApiContractAgent(Agent):
    name = "api-contract"
    title = "API Contract Review"
    summary = "Analyses API specs and suggests request validations, negative tests and schema checks."
    inputs_help = "an OpenAPI 3 spec (.yaml/.yml/.json)"
    example_files = ["orders_api.yaml"]
    output_model = ApiContractReview
    system_prompt = """Task: review an OpenAPI contract as an API test engineer.
For every endpoint propose: request validations the server must enforce (required fields,
types, formats, ranges, enums, lengths), negative tests with the exact request change and the
expected status code and error, and response schema checks to automate as contract tests
(e.g. with JSON Schema in REST Assured or Playwright). Use the locally computed gaps: explain the
risk of each and how to fix the spec. Do not invent endpoints that are not in the spec."""

    def analyse(self, files):
        spec_files = [f for f in files if f.suffix in (".yaml", ".yml", ".json")]
        if not spec_files:
            raise AgentError("api-contract needs an OpenAPI .yaml/.yml/.json file.")
        try:
            return analyse_spec(load_spec(spec_files[0].text()))
        except ValueError as exc:
            raise AgentError(str(exc)) from exc

    def build_prompt(self, files, facts):
        docs = "\n\n".join(file_block(f) for f in files)
        return f"{docs}\n\n{facts_block(facts)}\n\nReview this API contract."
