
import pytest

from app import tools


def test_ferramenta_nao_autorizada():
    with pytest.raises(ValueError, match="não autorizada"):
        tools.executar_ferramenta(
            "delete_all_orders"
        )


def test_argumentos_invalidos():
    with pytest.raises(ValueError, match="objeto"):
        tools.executar_ferramenta(
            "get_general_metrics",
            ["argumento_invalido"]
        )


def test_periodo_invertido():
    with pytest.raises(ValueError, match="data inicial"):
        tools.consultar_regioes_por_periodo(
            "2026-10-20",
            "2026-10-10"
        )


def test_ferramenta_geral(monkeypatch):
    indicadores = {
        "total_pedidos": 1000,
        "valor_total": 135544.32,
        "taxa_cancelamento": 8.9,
        "taxa_atraso": 9.9,
    }

    monkeypatch.setattr(
        tools,
        "get_indicadores_gerais",
        lambda: indicadores
    )

    resultado = tools.executar_ferramenta(
        "get_general_metrics"
    )

    assert resultado == indicadores
