from fastapi.testclient import TestClient
from app.main import app
from app import agent_api, agent

client = TestClient(app)


def test_context_forwarded(monkeypatch):
    def answer(message, history):
        assert message == 'E os atrasos?'
        assert history == [{'role': 'user', 'content': 'Compare as regiões'}]
        return 'Contexto recebido'
    monkeypatch.setattr(agent_api, 'perguntar_ao_agente', answer)
    response = client.post('/agent/chat', json={'message': 'E os atrasos?', 'history': [
        {'role': 'user', 'content': 'Compare as regiões'}]})
    assert response.status_code == 200


def test_context_bounds():
    for history in ([{'role': 'user', 'content': 'x'}] * 7,
                    [{'role': 'system', 'content': 'x'}],
                    [{'role': 'assistant', 'content': 'x' * 1501}]):
        assert client.post('/agent/chat', json={'message': 'Teste', 'history': history}).status_code == 422


def test_context_sent_as_sdk_history(monkeypatch):
    captured = {}
    class Chats:
        def create(self, **kwargs):
            captured.update(kwargs)
            return object()
    class FakeClient:
        chats = Chats()
        def __init__(self, **kwargs):
            pass
        def close(self):
            pass
    monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
    monkeypatch.setattr(agent.genai, 'Client', FakeClient)
    agent.criar_chat([{'role': 'user', 'content': 'Regiões'}, {'role': 'assistant', 'content': 'Dados'}])
    assert [item.role for item in captured['history']] == ['user', 'model']
    assert captured['history'][0].parts[0].text == 'Regiões'
