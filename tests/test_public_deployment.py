from fastapi.testclient import TestClient
from app.main import app
from app import agent_api

def test_public_chat_requires_free_tier_confirmation(monkeypatch):
    monkeypatch.setenv("APP_PUBLIC_DEPLOYMENT", "true")
    monkeypatch.delenv("GEMINI_FREE_TIER_CONFIRMED", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "must-not-be-used")
    def forbidden(*args, **kwargs):
        raise AssertionError("Gemini must not be called")
    monkeypatch.setattr(agent_api, "perguntar_ao_agente", forbidden)
    with TestClient(app) as client:
        response = client.post("/agent/chat", json={"message": "teste"})
    assert response.status_code == 503
    assert "gratuito" in response.json()["detail"]

def test_daily_budget_persists_between_connections(tmp_path):
    from app.chat_quota import reserve_request
    path = tmp_path / 'quota.sqlite3'
    assert reserve_request(path, limit=2)
    assert reserve_request(path, limit=2)
    assert not reserve_request(path, limit=2)
