
import pytest

from app import tools


def test_somente_ferramentas_autorizadas():
    """Verifica quais ferramentas o agente pode executar."""

    ferramentas_esperadas = {
        "get_general_metrics",
        "get_regions_metrics",
        "get_categories_metrics",
        "get_regions_by_period",
    }

    assert set(tools.FERRAMENTAS) == ferramentas_esperadas


@pytest.mark.parametrize(
    "nome",
    [
        "delete_all_orders",
        "execute_sql",
        "__import__",
        "drop_database",
    ],
)
def test_bloqueio_de_ferramentas_proibidas(nome):
    """Impede a execução de operações não autorizadas."""

    with pytest.raises(ValueError, match="não autorizada"):
        tools.executar_ferramenta(nome)


def test_fidelidade_dos_indicadores(monkeypatch):
    """Verifica se a ferramenta preserva os dados recebidos."""

    dados_banco = {
        "total_pedidos": 1000,
        "valor_total": 135544.32,
        "taxa_cancelamento": 8.9,
        "taxa_atraso": 9.9,
    }

    monkeypatch.setattr(
        tools,
        "get_indicadores_gerais",
        lambda: dados_banco,
    )

    resultado = tools.executar_ferramenta(
        "get_general_metrics"
    )

    assert resultado == dados_banco


def test_ferramenta_regional(monkeypatch):
    """Verifica o encaminhamento da consulta regional."""

    dados = [
        {"regiao": "Brasília", "total_pedidos": 120},
        {"regiao": "Curitiba", "total_pedidos": 80},
    ]

    monkeypatch.setattr(
        tools,
        "get_indicadores_por_regiao",
        lambda: dados,
    )

    resultado = tools.executar_ferramenta(
        "get_regions_metrics"
    )

    assert resultado == dados


def test_ferramenta_categoria(monkeypatch):
    """Verifica o encaminhamento da consulta por categoria."""

    dados = [
        {"categoria": "Restaurante", "total_pedidos": 50},
        {"categoria": "Mercado", "total_pedidos": 30},
    ]

    monkeypatch.setattr(
        tools,
        "get_indicadores_por_categoria",
        lambda: dados,
    )

    resultado = tools.executar_ferramenta(
        "get_categories_metrics"
    )

    assert resultado == dados


def test_periodo_encaminhado_corretamente(monkeypatch):
    """Confirma que as datas chegam corretamente à consulta."""

    def consulta_simulada(inicio, fim):
        assert inicio.isoformat() == "2026-10-10"
        assert fim.isoformat() == "2026-10-20"

        return [{"regiao": "Brasília", "total_pedidos": 50}]

    monkeypatch.setattr(
        tools,
        "get_regioes_por_periodo",
        consulta_simulada,
    )

    resultado = tools.executar_ferramenta(
        "get_regions_by_period",
        {
            "data_inicio": "2026-10-10",
            "data_fim": "2026-10-20",
        },
    )

    assert resultado[0]["total_pedidos"] == 50


def test_erro_em_consulta_nao_retorna_dados_falsos(
    monkeypatch,
):
    """Verifica se um erro é propagado, sem inventar dados."""

    def banco_indisponivel():
        raise ConnectionError("Banco indisponível")

    monkeypatch.setattr(
        tools,
        "get_indicadores_gerais",
        banco_indisponivel,
    )

    with pytest.raises(ConnectionError):
        tools.executar_ferramenta("get_general_metrics")
