
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resposta = client.get("/health")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"


def test_metrics():
    resposta = client.get("/metrics")

    assert resposta.status_code == 200

    dados = resposta.json()["data"]

    assert dados["total_pedidos"] == 1000


def test_metrics_regions():
    resposta = client.get("/metrics/regions")

    assert resposta.status_code == 200
    assert len(resposta.json()["data"]) == 5


def test_metrics_categories():
    resposta = client.get("/metrics/categories")

    assert resposta.status_code == 200
    assert len(resposta.json()["data"]) == 3


def test_invalid_period():
    resposta = client.get(
        "/metrics/period",
        params={
            "start_date": "2026-10-20",
            "end_date": "2026-10-10",
        },
    )

    assert resposta.status_code == 400


def test_valid_period():
    resposta = client.get(
        "/metrics/period",
        params={
            "start_date": "2026-10-10",
            "end_date": "2026-10-20",
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()["data"]["total_pedidos"] > 0
