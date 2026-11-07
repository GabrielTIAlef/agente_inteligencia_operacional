
import pytest

from app import tools


def test_data_inexistente():
    with pytest.raises(ValueError, match="inexistente"):
        tools.consultar_regioes_por_periodo(
            "2026-02-30",
            "2026-03-10",
        )


def test_formato_invalido():
    with pytest.raises(ValueError, match="formato"):
        tools.consultar_regioes_por_periodo(
            "10/10/2026",
            "20/10/2026",
        )


def test_periodo_muito_longo():
    with pytest.raises(ValueError, match="366 dias"):
        tools.consultar_regioes_por_periodo(
            "2025-01-01",
            "2026-10-20",
        )


def test_periodo_valido(monkeypatch):
    resultado_esperado = [
        {
            "regiao": "Brasília",
            "total_pedidos": 50,
        }
    ]

    def consulta_simulada(inicio, fim):
        assert inicio.isoformat() == "2026-10-10"
        assert fim.isoformat() == "2026-10-20"
        return resultado_esperado

    monkeypatch.setattr(
        tools,
        "get_regioes_por_periodo",
        consulta_simulada,
    )

    resultado = tools.consultar_regioes_por_periodo(
        "2026-10-10",
        "2026-10-20",
    )

    assert resultado == resultado_esperado
