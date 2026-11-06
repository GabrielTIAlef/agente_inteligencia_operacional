
from datetime import date

from app.analytics import (
    calcular_indicadores,
    calcular_por_regiao,
    calcular_por_categoria,
    filtrar_por_periodo,
)


def criar_pedidos_teste():
    """Cria registros pequenos com resultados conhecidos."""

    return [
        {
            "pedido_id": "1",
            "data_pedido": "2026-10-10",
            "regiao": "Brasília",
            "categoria": "Restaurante",
            "valor": "100.00",
            "status": "entregue",
        },
        {
            "pedido_id": "2",
            "data_pedido": "2026-10-11",
            "regiao": "Brasília",
            "categoria": "Mercado",
            "valor": "50.00",
            "status": "cancelado",
        },
        {
            "pedido_id": "3",
            "data_pedido": "2026-10-12",
            "regiao": "São Paulo",
            "categoria": "Restaurante",
            "valor": "80.00",
            "status": "em_atraso",
        },
        {
            "pedido_id": "4",
            "data_pedido": "2026-10-20",
            "regiao": "São Paulo",
            "categoria": "Mercado",
            "valor": "70.00",
            "status": "entregue",
        },
    ]


def test_indicadores_gerais():
    pedidos = criar_pedidos_teste()

    resultado = calcular_indicadores(pedidos)

    assert resultado["total_pedidos"] == 4
    assert resultado["valor_total"] == 300.0
    assert resultado["taxa_cancelamento"] == 25.0
    assert resultado["taxa_atraso"] == 25.0


def test_lista_vazia():
    resultado = calcular_indicadores([])

    assert resultado["total_pedidos"] == 0
    assert resultado["valor_total"] == 0.0
    assert resultado["taxa_cancelamento"] == 0.0
    assert resultado["taxa_atraso"] == 0.0


def test_indicadores_por_regiao():
    pedidos = criar_pedidos_teste()

    resultado = calcular_por_regiao(pedidos)

    regioes = {
        item["regiao"]: item
        for item in resultado
    }

    assert regioes["Brasília"]["total_pedidos"] == 2
    assert regioes["Brasília"]["taxa_cancelamento"] == 50.0

    assert regioes["São Paulo"]["total_pedidos"] == 2
    assert regioes["São Paulo"]["taxa_atraso"] == 50.0


def test_indicadores_por_categoria():
    pedidos = criar_pedidos_teste()

    resultado = calcular_por_categoria(pedidos)

    categorias = {
        item["categoria"]: item
        for item in resultado
    }

    assert categorias["Restaurante"]["total_pedidos"] == 2
    assert categorias["Restaurante"]["taxa_atraso"] == 50.0

    assert categorias["Mercado"]["total_pedidos"] == 2
    assert categorias["Mercado"]["taxa_cancelamento"] == 50.0


def test_filtro_por_periodo():
    pedidos = criar_pedidos_teste()

    resultado = filtrar_por_periodo(
        pedidos,
        date(2026, 10, 10),
        date(2026, 10, 12),
    )

    assert len(resultado) == 3


def test_filtro_inclui_datas_limite():
    pedidos = criar_pedidos_teste()

    resultado = filtrar_por_periodo(
        pedidos,
        date(2026, 10, 20),
        date(2026, 10, 20),
    )

    assert len(resultado) == 1
    assert resultado[0]["pedido_id"] == "4"
