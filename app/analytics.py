
import csv
from pathlib import Path

# Identifica a pasta principal do projeto.
BASE_DIR = Path(__file__).resolve().parent.parent

# Localiza nosso arquivo com os pedidos fictícios.
CSV_PATH = BASE_DIR / "data" / "synthetic" / "pedidos.csv"


def carregar_pedidos():
    """Lê o CSV e devolve uma lista de pedidos."""

    with CSV_PATH.open("r", encoding="utf-8", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        pedidos = list(leitor)

    return pedidos


def calcular_indicadores(pedidos):
    """Calcula os principais indicadores operacionais."""

    total_pedidos = len(pedidos)

    if total_pedidos == 0:
        return {
            "total_pedidos": 0,
            "valor_total": 0.0,
            "taxa_cancelamento": 0.0,
            "taxa_atraso": 0.0
        }

    cancelados = sum(
        1 for pedido in pedidos
        if pedido["status"] == "cancelado"
    )

    atrasados = sum(
        1 for pedido in pedidos
        if pedido["status"] == "em_atraso"
    )

    valor_total = sum(
        float(pedido["valor"])
        for pedido in pedidos
    )

    return {
        "total_pedidos": total_pedidos,
        "valor_total": round(valor_total, 2),
        "taxa_cancelamento": round(
            cancelados / total_pedidos * 100, 2
        ),
        "taxa_atraso": round(
            atrasados / total_pedidos * 100, 2
        )
    }


from collections import defaultdict


def calcular_por_regiao(pedidos):
    """Calcula indicadores operacionais por região."""

    regioes = defaultdict(list)

    for pedido in pedidos:
        regioes[pedido["regiao"]].append(pedido)

    resultado = []

    for regiao, pedidos_regiao in regioes.items():
        indicadores = calcular_indicadores(pedidos_regiao)

        resultado.append({
            "regiao": regiao,
            **indicadores
        })

    return sorted(
        resultado,
        key=lambda item: item["taxa_cancelamento"],
        reverse=True
    )


def calcular_por_categoria(pedidos):
    """Calcula indicadores operacionais por categoria."""

    categorias = defaultdict(list)

    for pedido in pedidos:
        categorias[pedido["categoria"]].append(pedido)

    resultado = []

    for categoria, pedidos_categoria in categorias.items():
        indicadores = calcular_indicadores(pedidos_categoria)

        resultado.append({
            "categoria": categoria,
            **indicadores
        })

    return sorted(
        resultado,
        key=lambda item: item["taxa_atraso"],
        reverse=True
    )


if __name__ == "__main__":
    pedidos = carregar_pedidos()
    indicadores = calcular_indicadores(pedidos)

    print("\n=== INDICADORES OPERACIONAIS ===")

    for nome, valor in indicadores.items():
        print(f"{nome}: {valor}")

