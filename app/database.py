
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
