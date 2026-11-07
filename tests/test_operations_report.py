from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg import OperationalError

from app import reports
from app.access import LOCAL_ORIGINS, local_access
from app.main import app


def test_report_includes_all_breakdowns_and_trace(monkeypatch):
    monkeypatch.setattr(reports, "get_operations_snapshot", lambda: {
        "summary": {"total_pedidos": 1},
        "regions": [{"regiao": "Sul"}],
        "categories": [{"categoria": "Mercado"}],
    })
    response = TestClient(app).get("/reports/operations", headers={"Origin": LOCAL_ORIGINS[0]})
    assert response.status_code == 200
    payload = response.json()
    assert payload["request_id"] == response.headers["X-Request-ID"]
    assert response.headers["Access-Control-Allow-Origin"] == LOCAL_ORIGINS[0]
    assert payload["source"] == "postgresql"
    assert payload["summary"]["total_pedidos"] == 1
    assert payload["regions"] == [{"regiao": "Sul"}]
    assert payload["categories"] == [{"categoria": "Mercado"}]


def test_database_error_is_sanitized(monkeypatch):
    def fail():
        raise OperationalError("confidential database connection details")

    monkeypatch.setattr(reports, "get_operations_snapshot", fail)
    response = TestClient(app).get("/reports/operations")
    assert response.status_code == 503
    assert "confidential" not in response.text
    assert response.headers["X-Request-ID"]


def test_rejects_disallowed_origin_and_host():
    client = TestClient(app)
    assert client.get("/health", headers={"Origin": "https://example.org"}).status_code == 403
    assert client.get("/health", headers={"Host": "example.org"}).status_code == 400


def test_chat_body_size_media_type_and_rate_limit():
    isolated_app = FastAPI()
    isolated_app.middleware("http")(local_access(LOCAL_ORIGINS))

    @isolated_app.post("/agent/chat")
    def chat(payload: dict):
        return payload

    client = TestClient(isolated_app)
    assert client.post("/agent/chat", content="text").status_code == 415
    response = client.post("/agent/chat", json={"message": "x" * 8192})
    assert response.status_code == 413
    for _ in range(11):
        assert client.post("/agent/chat", json={"message": "ok"}).json() == {"message": "ok"}
    assert client.post("/agent/chat", json={"message": "ok"}).status_code == 429
