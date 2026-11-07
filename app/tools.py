
from datetime import date
import re
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
    """Consulta indicadores regionais em um período válido."""

    formato = r"\d{4}-\d{2}-\d{2}"

    if (
        not isinstance(data_inicio, str)
        or not isinstance(data_fim, str)
        or not re.fullmatch(formato, data_inicio)
        or not re.fullmatch(formato, data_fim)
    ):
        raise ValueError(
            "As datas devem estar no formato AAAA-MM-DD."
        )

    try:
        inicio = date.fromisoformat(data_inicio)
        fim = date.fromisoformat(data_fim)
    except ValueError as erro:
        raise ValueError(
            "Foi informada uma data inexistente."
        ) from erro

    if inicio > fim:
        raise ValueError(
            "A data inicial não pode ser posterior à final."
        )

    if (fim - inicio).days > 366:
        raise ValueError(
            "O período não pode ultrapassar 366 dias."
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
