import uvicorn

from etl.load_orders import carregar_pedidos, conectar_banco
from etl.migrate import migrate


if __name__ == "__main__":
    migrate()
    with conectar_banco() as connection:
        seed = not connection.execute("SELECT EXISTS (SELECT 1 FROM pedidos)").fetchone()[0]
    if seed:
        carregar_pedidos()
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, proxy_headers=False)
