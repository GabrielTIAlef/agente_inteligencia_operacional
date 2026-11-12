"""Aplica o schema sem recarregar ou substituir os pedidos existentes."""
from etl.load_orders import BASE_DIR, conectar_banco


def migrate():
    with conectar_banco() as connection:
        connection.execute("SET LOCAL lock_timeout = '5s'")
        connection.execute("SET LOCAL statement_timeout = '30s'")
        connection.execute("SELECT pg_advisory_xact_lock(7204, 0)")
        connection.execute((BASE_DIR / 'etl' / 'schema.sql').read_text(encoding='utf-8'))
    print('Schema aplicado. Nenhuma carga ou exclusão de pedidos foi executada.')


if __name__ == '__main__':
    migrate()
