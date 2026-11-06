
from decimal import Decimal

from etl.load_orders import conectar_banco


def get_indicadores_gerais():
    """Consulta indicadores diretamente no PostgreSQL."""

    sql = """
        SELECT
            COUNT(*) AS total_pedidos,
            COALESCE(SUM(valor), 0) AS valor_total,
            COALESCE(
                ROUND(
                    100.0 * COUNT(*) FILTER (
                        WHERE status = 'cancelado'
                    ) / NULLIF(COUNT(*), 0),
                    2
                ),
                0
            ) AS taxa_cancelamento,
            COALESCE(
                ROUND(
                    100.0 * COUNT(*) FILTER (
                        WHERE status = 'em_atraso'
                    ) / NULLIF(COUNT(*), 0),
                    2
                ),
                0
            ) AS taxa_atraso
        FROM pedidos;
    """

    with conectar_banco() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(sql)
            resultado = cursor.fetchone()

    return {
        "total_pedidos": resultado[0],
        "valor_total": float(resultado[1]),
        "taxa_cancelamento": float(resultado[2]),
        "taxa_atraso": float(resultado[3]),
    }


def get_indicadores_por_regiao():
    """Consulta indicadores agrupados por região."""

    sql = """
        SELECT
            regiao,
            COUNT(*) AS total_pedidos,
            COALESCE(SUM(valor), 0) AS valor_total,
            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE status = 'cancelado'
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS taxa_cancelamento,
            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE status = 'em_atraso'
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS taxa_atraso
        FROM pedidos
        GROUP BY regiao
        ORDER BY taxa_cancelamento DESC, regiao;
    """

    with conectar_banco() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(sql)
            resultados = cursor.fetchall()

    return [
        {
            "regiao": linha[0],
            "total_pedidos": linha[1],
            "valor_total": float(linha[2]),
            "taxa_cancelamento": float(linha[3]),
            "taxa_atraso": float(linha[4]),
        }
        for linha in resultados
    ]


def get_indicadores_por_categoria():
    """Consulta indicadores agrupados por categoria."""

    sql = """
        SELECT
            categoria,
            COUNT(*) AS total_pedidos,
            COALESCE(SUM(valor), 0) AS valor_total,
            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE status = 'cancelado'
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS taxa_cancelamento,
            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE status = 'em_atraso'
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS taxa_atraso
        FROM pedidos
        GROUP BY categoria
        ORDER BY taxa_atraso DESC, categoria;
    """

    with conectar_banco() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(sql)
            resultados = cursor.fetchall()

    return [
        {
            "categoria": linha[0],
            "total_pedidos": linha[1],
            "valor_total": float(linha[2]),
            "taxa_cancelamento": float(linha[3]),
            "taxa_atraso": float(linha[4]),
        }
        for linha in resultados
    ]


def get_regioes_por_periodo(data_inicio, data_fim):
    """Consulta indicadores regionais em um intervalo."""

    sql = """
        SELECT
            regiao,
            COUNT(*) AS total_pedidos,
            COALESCE(SUM(valor), 0) AS valor_total,
            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE status = 'cancelado'
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS taxa_cancelamento,
            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE status = 'em_atraso'
                ) / NULLIF(COUNT(*), 0),
                2
            ) AS taxa_atraso
        FROM pedidos
        WHERE data_pedido BETWEEN %s AND %s
        GROUP BY regiao
        ORDER BY taxa_cancelamento DESC, regiao;
    """

    with conectar_banco() as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(sql, (data_inicio, data_fim))
            resultados = cursor.fetchall()

    return [
        {
            "regiao": linha[0],
            "total_pedidos": linha[1],
            "valor_total": float(linha[2]),
            "taxa_cancelamento": float(linha[3]),
            "taxa_atraso": float(linha[4]),
        }
        for linha in resultados
    ]
