import csv
import os
from datetime import date
from decimal import Decimal
from pathlib import Path

import psycopg
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "synthetic" / "pedidos.csv"

load_dotenv(BASE_DIR / ".env")


def conectar_banco(*, somente_leitura=False):
    """Abre uma conexão com o PostgreSQL."""

    names = ("host", "port", "dbname", "user", "password")
    keys = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
    try:
        config = {name: os.environ[key] for name, key in zip(names, keys)}
    except KeyError as error:
        raise psycopg.OperationalError("Configuração do PostgreSQL incompleta.") from error

    if somente_leitura:
        config["options"] = "-c default_transaction_read_only=on -c statement_timeout=5000"
    return psycopg.connect(**config, connect_timeout=5)


def extrair_pedidos():
    """Extrai os registros do arquivo CSV."""

    with CSV_PATH.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as arquivo:
        return list(csv.DictReader(arquivo))


def transformar_pedido(pedido):
    """Converte e valida um registro."""

    pedido_id = int(pedido["pedido_id"])
    data_pedido = date.fromisoformat(pedido["data_pedido"])
    regiao = pedido["regiao"].strip()
    categoria = pedido["categoria"].strip()
    valor = Decimal(pedido["valor"])
    status = pedido["status"].strip()

    if pedido_id <= 0:
        raise ValueError("ID de pedido inválido")

    if not regiao or not categoria:
        raise ValueError("Região ou categoria vazia")

    if not valor.is_finite() or valor < 0:
        raise ValueError("Valor inválido")

    if status not in {"entregue", "cancelado", "em_atraso"}:
        raise ValueError("Status inválido")

    return (
        pedido_id,
        data_pedido,
        regiao,
        categoria,
        valor,
        status,
    )


def carregar_pedidos():
    """Insere ou atualiza registros no PostgreSQL."""

    registros_csv = extrair_pedidos()
    registros = [
        transformar_pedido(pedido)
        for pedido in registros_csv
    ]

    ids = [registro[0] for registro in registros]

    if len(ids) != len(set(ids)):
        raise ValueError("IDs duplicados no arquivo CSV")

    comando_sql = """
        INSERT INTO pedidos (
            pedido_id,
            data_pedido,
            regiao,
            categoria,
            valor,
            status
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (pedido_id)
        DO UPDATE SET
            data_pedido = EXCLUDED.data_pedido,
            regiao = EXCLUDED.regiao,
            categoria = EXCLUDED.categoria,
            valor = EXCLUDED.valor,
            status = EXCLUDED.status
    """

    with conectar_banco() as conexao:
        with conexao.cursor() as cursor:
            cursor.executemany(comando_sql, registros)

        # O contexto da conexão confirma a transação
        # caso não tenha ocorrido nenhum erro.

    print("Carga finalizada com sucesso!")
    print(f"Registros processados: {len(registros)}")


if __name__ == "__main__":
    carregar_pedidos()
