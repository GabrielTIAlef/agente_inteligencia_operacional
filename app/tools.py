
from datetime import date

from app.database import (
    get_indicadores_gerais,
    get_indicadores_por_regiao,
    get_indicadores_por_categoria,
    get_regioes_por_periodo,
)


def consultar_indicadores_gerais():
    """Consulta os indicadores gerais do marketplace."""

    return get_indicadores_gerais()


def consultar_indicadores_regionais():
    """Consulta os indicadores agrupados por região."""

    return get_indicadores_por_regiao()


def consultar_indicadores_categorias():
    """Consulta os indicadores agrupados por categoria."""

    return get_indicadores_por_categoria()


def consultar_regioes_por_periodo(
    data_inicio: str,
    data_fim: str
):
    """Consulta indicadores regionais em um período."""

    inicio = date.fromisoformat(data_inicio)
    fim = date.fromisoformat(data_fim)

    if inicio > fim:
        raise ValueError(
            "A data inicial não pode ser posterior à final."
        )

    return get_regioes_por_periodo(inicio, fim)


# Lista explícita de ferramentas permitidas.
FERRAMENTAS = {
    "get_general_metrics": consultar_indicadores_gerais,
    "get_regions_metrics": consultar_indicadores_regionais,
    "get_categories_metrics": consultar_indicadores_categorias,
    "get_regions_by_period": consultar_regioes_por_periodo,
}


def executar_ferramenta(nome: str, argumentos: dict | None = None):
    """Executa somente ferramentas previamente autorizadas."""

    if nome not in FERRAMENTAS:
        raise ValueError(f"Ferramenta não autorizada: {nome}")

    if argumentos is None:
        argumentos = {}

    if not isinstance(argumentos, dict):
        raise ValueError("Os argumentos devem ser um objeto.")

    ferramenta = FERRAMENTAS[nome]

    return ferramenta(**argumentos)
