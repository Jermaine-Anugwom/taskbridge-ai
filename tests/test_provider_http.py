"""Real loopback HTTP transport, scripted responses. No live model or external network."""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from conftest import workflow_payload
from taskbridge.engine import capture_workflow
from taskbridge.model_providers import OpenAICompatibleModel
from taskbridge.model_runtime import run_model_analysis
from test_model_provider import response_payload


@pytest.fixture
def loopback_server():
    replies = []
    received = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            received.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            status, payload = replies.pop(0)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode())

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1/chat/completions", replies, received
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize("failure", [None, "missing-usage", "schema", "evidence"])
def test_http_trace_accounting_through_real_transport(loopback_server, failure):
    endpoint, replies, received = loopback_server
    payload = json.loads(response_payload())
    if failure == "missing-usage":
        payload.pop("usage")
    elif failure in {"schema", "evidence"}:
        call = payload["choices"][0]["message"]["tool_calls"][0]["function"]
        output = json.loads(call["arguments"])
        if failure == "schema":
            output.pop("summary")
        else:
            output["summary_evidence_ids"] = ["ev-invented"]
        call["arguments"] = json.dumps(output)
    replies.append((200, payload))
    trace = run_model_analysis(capture_workflow(workflow_payload(), "wf-http"),
        "Analyze the synthetic workflow.", OpenAICompatibleModel(endpoint, "fixture", max_retries=0))
    assert len(received) == 1
    assert received[0]["tool_choice"]["function"]["name"] == "record_workflow_analysis"
    assert trace.usage.input_tokens == (None if failure == "missing-usage" else 612)
    assert trace.status.value == ("fallback" if failure in {"schema", "evidence"} else "succeeded")
    assert trace.attempts[0].model == "fixture-model-2026-09"


def test_http_retry_usage_is_not_silently_zero(loopback_server, monkeypatch):
    endpoint, replies, received = loopback_server
    replies.extend([(503, {"error": "synthetic transient failure"}), (200, json.loads(response_payload()))])
    monkeypatch.setattr("time.sleep", lambda _: None)
    trace = run_model_analysis(capture_workflow(workflow_payload(), "wf-http"),
        "Analyze the synthetic workflow.", OpenAICompatibleModel(endpoint, "fixture", max_retries=1))
    assert len(received) == 2
    assert trace.retry_count == 1
    assert trace.usage.input_tokens is None
    assert trace.reported_usage.input_tokens == 612
    assert trace.attempts[0].error_category == "HTTP503"


def test_http_error_with_usage_preserves_consumption(loopback_server):
    endpoint, replies, _ = loopback_server
    replies.append((400, {"usage": {"prompt_tokens": 80, "completion_tokens": 0}, "error": "fixture"}))
    trace = run_model_analysis(capture_workflow(workflow_payload(), "wf-http"),
        "Analyze the synthetic workflow.", OpenAICompatibleModel(endpoint, "fixture", max_retries=0))
    assert trace.status.value == "fallback"
    assert trace.usage.input_tokens == 80
    assert trace.usage.output_tokens == 0
