from datetime import date
from decimal import Decimal

from app.dashboard import summarize
from app.monitor import detect, narrative


def test_empty_dashboard_has_undefined_rates():
    summary = summarize([])
    assert summary["average"] is None
    assert summary["cancellation"] is None
    assert summary["value"] == 0


def test_rules_use_unrounded_rates_and_minimum_samples():
    row = (date(2026, 1, 1), "Sul", "Casa", Decimal("20"), "cancelado")
    delivered = (*row[:4], "entregue")
    summary = summarize([row] * 3 + [delivered] * 27)
    report = {"summary": summary, "previous": {"orders": 50}}
    assert summary["value"] == 600
    assert [alert["label"] for alert in detect(report)] == ["Cancelamento", "Queda no volume"]
    assert not detect({"summary": summarize([row] * 29), "previous": None})


def test_gemini_is_off_by_default(monkeypatch):
    monkeypatch.delenv("MONITOR_GEMINI_ENABLED", raising=False)
    assert narrative({"summary": {"orders": 50}}, [{"label": "Atraso"}])[1] == "determinístico"


def test_gemini_failure_returns_deterministic_summary(monkeypatch):
    from app import monitor

    def unavailable(**kwargs):
        raise TimeoutError("simulated timeout")

    monkeypatch.setattr(monitor.genai, "Client", unavailable)
    monkeypatch.setenv("MONITOR_GEMINI_ENABLED", "true")
    monkeypatch.setenv("MONITOR_GEMINI_MODEL", "test-model")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    summary, method = narrative({"summary": {"orders": 50}}, [{"label": "Atraso"}])
    assert method == "fallback"
    assert "50 pedidos" in summary
