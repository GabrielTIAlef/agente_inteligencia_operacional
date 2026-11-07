from fastapi.testclient import TestClient
from google.genai.errors import ClientError

from app.main import app
from app import agent_api


client = TestClient(app)


def test_chat_sucesso(monkeypatch):
    def agente_simulado(pergunta):
        assert pergunta == "Quantos pedidos existem?"
        return "Existem 1.000 pedidos."

    monkeypatch.setattr(
        agent_api,
        "perguntar_ao_agente",
        agente_simulado,
    )

    resposta = client.post(
        "/agent/chat",
        json={"message": "Quantos pedidos existem?"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "success"
    assert resposta.json()["response"] == "Existem 1.000 pedidos."


def test_chat_mensagem_vazia():
    resposta = client.post(
        "/agent/chat",
        json={"message": ""},
    )

    assert resposta.status_code == 422


def test_chat_apenas_espacos():
    resposta = client.post(
        "/agent/chat",
        json={"message": "   "},
    )

    assert resposta.status_code == 422


def test_chat_mensagem_muito_grande():
    resposta = client.post(
        "/agent/chat",
        json={"message": "A" * 501},
    )

    assert resposta.status_code == 422


def test_chat_erro_interno(monkeypatch):
    def agente_com_erro(pergunta):
        raise RuntimeError("Erro interno simulado")

    monkeypatch.setattr(
        agent_api,
        "perguntar_ao_agente",
        agente_com_erro,
    )

    resposta = client.post(
        "/agent/chat",
        json={"message": "Teste de erro"},
    )

    assert resposta.status_code == 503
    assert "Erro interno simulado" not in resposta.text


def test_chat_limite_gemini(monkeypatch):
    def agente_sem_cota(pergunta):
        raise ClientError(
            429,
            {
                "error": {
                    "code": 429,
                    "message": "Quota exceeded",
                    "status": "RESOURCE_EXHAUSTED",
                }
            },
            None,
        )

    monkeypatch.setattr(
        agent_api,
        "perguntar_ao_agente",
        agente_sem_cota,
    )

    resposta = client.post(
        "/agent/chat",
        json={"message": "Quantos pedidos existem?"},
    )

    assert resposta.status_code == 429
    assert "limite" in resposta.json()["detail"].lower()
