import pytest
from fastapi.testclient import TestClient

from app.core.config import ROOT, Settings
from app.main import create_app
from app.retrieval.access_control import AccessController


@pytest.fixture
def client():
    with TestClient(
        create_app(
            Settings(_env_file=None, rag_mode="local", access_level="EMPLOYEE", technova_api_key="")
        )
    ) as client:
        yield client


def test_app_and_status(client):
    assert client.get("/").status_code == 200
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/health").json() == {"status": "ok"}
    status = client.get("/api/status").json()
    docs = client.get("/api/documents").json()["documents"]
    assert status["mode"] == "local"
    assert status["document_count"] == len(docs) > 0
    assert sum(status["departments"].values()) == len(docs)
    assert all(d["access_level"] == "EMPLOYEE" for d in docs)


def test_question_sources_resolve(client):
    result = client.post(
        "/api/query", json={"query": "How many days of annual leave do employees receive?"}
    )
    assert result.status_code == 200
    data = result.json()
    assert "24 days" in data["answer"]
    assert data["grounded"] is True
    assert data["mode"] == "local"
    assert "hr_leave_001" in [s["document_id"] for s in data["sources"]]
    for source in data["sources"]:
        document = client.get(f"/api/documents/{source['document_id']}").json()
        assert document["title"] == source["title"]
        assert source["excerpt"] in document["content"]


@pytest.mark.parametrize(
    "payload",
    [
        {"query": ""},
        {"query": "   "},
        {"query": "x" * 2001},
        {},
        {"query": "leave", "user_access_level": "ADMIN"},
    ],
)
def test_invalid_questions(client, payload):
    assert client.post("/api/query", json=payload).status_code == 422


def test_unknown_question(client):
    result = client.post("/api/query", json={"query": "quantum teleportation interstellar"}).json()
    assert not result["grounded"]
    assert result["sources"] == []
    assert "couldn’t find" in result["answer"]


def test_document_search_and_permissions(client):
    docs = client.get(
        "/api/documents", params={"search": "annual leave", "department": "HR"}
    ).json()["documents"]
    assert [d["document_id"] for d in docs] == ["hr_leave_001"]
    assert client.get("/api/documents", params={"department": "AI & ML"}).json()["documents"] == []
    assert client.get("/api/documents/ai_rag_001").status_code == 404
    restricted = next(
        d
        for d in client.app.state.knowledge.documents.values()
        if d.metadata.access_level != "EMPLOYEE"
    )
    assert client.get(f"/api/documents/{restricted.metadata.document_id}").status_code == 404
    assert client.get("/api/documents/not-a-document").status_code == 404


def test_workspace_auth():
    app = create_app(
        Settings(_env_file=None, rag_mode="local", technova_api_key="synthetic-test-key")
    )
    with TestClient(app) as client:
        for path in ("/api/status", "/api/documents", "/api/documents/hr_leave_001"):
            assert client.get(path).status_code == 401
        assert client.post("/api/query", json={"query": "leave"}).status_code == 401
        assert client.get("/api/status", headers={"X-API-Key": "wrong"}).status_code == 401
        assert (
            client.get("/api/status", headers={"X-API-Key": "synthetic-test-key"}).status_code
            == 200
        )
        assert client.get("/health").status_code == 200


@pytest.mark.parametrize(
    "role", ["EMPLOYEE", "MANAGER", "AI_ENGINEER", "DEVOPS", "SECURITY", "ADMIN"]
)
def test_access_at_every_boundary(role):
    controller = AccessController()
    with TestClient(
        create_app(Settings(_env_file=None, rag_mode="local", access_level=role))
    ) as client:
        visible = client.get("/api/documents").json()["documents"]
        expected = [
            d
            for d in client.app.state.knowledge.documents.values()
            if controller.can_access(role, d.metadata.access_level)
        ]
        assert len(visible) == len(expected)
        for d in client.app.state.knowledge.documents.values():
            response = client.get(f"/api/documents/{d.metadata.document_id}")
            assert response.status_code == (200 if d in expected else 404)
        data = client.post(
            "/api/query", json={"query": "security monitoring deployment RAG leave"}
        ).json()
        assert all(
            client.get(f"/api/documents/{s['document_id']}").status_code == 200
            for s in data["sources"]
        )


def test_specialty_roles_do_not_grant_other_specialties():
    controller = AccessController()
    assert not controller.can_access("AI_ENGINEER", "SECURITY")
    assert not controller.can_access("DEVOPS", "AI_ENGINEER")
    assert controller.can_access("ADMIN", "SECURITY")
    with pytest.raises(ValueError):
        controller.can_access("unknown", "EMPLOYEE")


def test_empty_library(tmp_path):
    with TestClient(
        create_app(Settings(_env_file=None, knowledge_dir=tmp_path, rag_mode="local"))
    ) as client:
        assert client.get("/api/status").json()["document_count"] == 0
        assert client.get("/api/documents").json()["documents"] == []
        assert client.post("/api/query", json={"query": "leave"}).json()["sources"] == []


def test_errors_and_backpressure(client, monkeypatch):
    def fail(_):
        raise RuntimeError("private provider error")

    monkeypatch.setattr(client.app.state.knowledge, "query", fail)
    response = client.post("/api/query", json={"query": "leave"})
    assert response.status_code == 503
    assert "private provider" not in response.text
    slots = client.app.state.query_slots
    assert slots.acquire(blocking=False)
    assert slots.acquire(blocking=False)
    try:
        assert client.post("/api/query", json={"query": "leave"}).status_code == 429
    finally:
        slots.release()
        slots.release()


def test_duplicate_documents_fail_startup(tmp_path):
    source = (ROOT / "data/raw/hr/leave_policy.md").read_text()
    (tmp_path / "one.md").write_text(source)
    (tmp_path / "two.md").write_text(source)
    with pytest.raises(ValueError, match="Duplicate document ID"):
        with TestClient(create_app(Settings(_env_file=None, knowledge_dir=tmp_path))):
            pass


def test_groq_requires_explicit_key():
    with pytest.raises(ValueError, match="requires GROQ_API_KEY"):
        with TestClient(create_app(Settings(_env_file=None, rag_mode="groq", groq_api_key=""))):
            pass
