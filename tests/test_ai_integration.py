"""Opt-in real model/graph test with synthetic Groq SDK responses.

Install requirements-ai.txt, then run RUN_AI_INTEGRATION=1 pytest -q.
Model downloads are required on first run; no live provider credential is used.
"""

import json
import os

import httpx
import pytest


@pytest.mark.skipif(
    os.getenv("RUN_AI_INTEGRATION") != "1",
    reason="Opt-in AI test requires models and optional dependencies",
)
def test_real_graph_retry_and_trace_isolation(tmp_path, monkeypatch):
    pytest.importorskip("langgraph")
    pytest.importorskip("sentence_transformers")
    from groq import Groq
    from app.core.config import Settings
    from app.services.knowledge import KnowledgeService

    monkeypatch.setenv("GROQ_API_KEY", "synthetic-local-test")
    monkeypatch.chdir(tmp_path)
    verification_count = 0

    def respond(request):
        nonlocal verification_count
        body = json.loads(request.content)
        system = body["messages"][0]["content"]
        if "query routing component" in system:
            content = json.dumps({"route": "DIRECT", "retrieval_query": "annual leave"})
        elif "query rewriting component" in system:
            content = "annual leave days employees"
        elif "grounding verifier" in system:
            verification_count += 1
            content = json.dumps(
                {
                    "grounded": verification_count > 1,
                    "claims": [],
                    "reason": "Synthetic verifier test",
                }
            )
        else:
            content = (
                "Eligible full-time employees receive 24 days of annual leave per calendar year."
            )
        return httpx.Response(
            200,
            json={
                "id": "synthetic-completion",
                "object": "chat.completion",
                "created": 0,
                "model": body["model"],
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": content},
                    }
                ],
            },
        )

    service = KnowledgeService(
        Settings(
            _env_file=None,
            rag_mode="groq",
            groq_api_key="synthetic-local-test",
            access_level="EMPLOYEE",
            vectorstore_dir=tmp_path / "index",
        )
    )
    with Groq(
        api_key="synthetic-local-test",
        http_client=httpx.Client(transport=httpx.MockTransport(respond)),
    ) as client:
        nodes = service.graph.nodes
        for component in (
            nodes.query_pipeline.router,
            nodes.query_pipeline.rewriter,
            nodes.query_rewriter,
            nodes.generator,
            nodes.verifier,
        ):
            component.client = client
        result = service.query("How many days of annual leave do employees receive?")
        assert result["mode"] == "groq" and result["grounded"]
        assert result["retry_count"] == 1
        assert "24 days" in result["answer"]
        assert result["sources"]
        assert all(service.document(s["document_id"]) for s in result["sources"])
        second = service.query("What is the annual leave policy?")
        assert second["retry_count"] == 0 and second["grounded"]
        assert nodes.tracer.trace["query"] == "What is the annual leave policy?"
