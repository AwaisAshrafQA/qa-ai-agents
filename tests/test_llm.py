"""ClaudeClient against a mocked HTTP transport: request shape, parsing and error handling."""

import json

import anthropic
import httpx2
import pytest

from qa_agents.agents.failure_analysis import FailureAnalysis
from qa_agents.core.llm import AgentError, ClaudeClient

DEMO = {"summary": "One defect.", "failures": [], "patterns": []}


def make_client(stop_reason="end_turn", status=200, text=json.dumps(DEMO)):
    sent = []

    def handler(request):
        sent.append(json.loads(request.content))
        if status != 200:
            return httpx2.Response(status, json={"type": "error", "error": {"type": "error", "message": "nope"}})
        return httpx2.Response(200, json={
            "id": "msg_test", "type": "message", "role": "assistant", "model": "claude-opus-5-5",
            "content": [{"type": "text", "text": text}], "stop_reason": stop_reason, "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 10},
        })

    http = anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(handler))
    sdk = anthropic.Anthropic(api_key="test-key", base_url="http://stub.localhost", http_client=http, max_retries=0)
    return ClaudeClient(client=sdk, effort="medium"), sent


def test_request_shape_and_parsed_output():
    llm, sent = make_client()
    out = llm.run(agent="failure-analysis", system="sys", prompt="hello", schema=FailureAnalysis)
    assert isinstance(out, FailureAnalysis) and out.summary == "One defect."
    body = sent[0]
    assert body["model"] == "claude-opus-5-5"
    assert body["system"] == "sys"
    assert body["output_config"]["effort"] == "medium"
    assert body["output_config"]["format"]["type"] == "json_schema"
    assert body["messages"] == [{"role": "user", "content": "hello"}]


def test_refusal_is_reported():
    llm, _ = make_client(stop_reason="refusal", text="")
    with pytest.raises(AgentError, match="declined"):
        llm.run(agent="x", system="s", prompt="p", schema=FailureAnalysis)


def test_truncation_is_reported():
    llm, _ = make_client(stop_reason="max_tokens", text='{"summary": "cut')
    with pytest.raises(AgentError, match="incomplete"):
        llm.run(agent="x", system="s", prompt="p", schema=FailureAnalysis)


def test_valid_json_with_refusal_stop_reason_is_still_rejected():
    llm, _ = make_client(stop_reason="refusal")
    with pytest.raises(AgentError, match="declined"):
        llm.run(agent="x", system="s", prompt="p", schema=FailureAnalysis)


def test_invalid_key_is_reported():
    llm, _ = make_client(status=401)
    with pytest.raises(AgentError, match="invalid"):
        llm.run(agent="x", system="s", prompt="p", schema=FailureAnalysis)
