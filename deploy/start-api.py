from pathlib import Path

import uvicorn

from etl.load_orders import carregar_pedidos, conectar_banco


if __name__ == "__main__":
    with conectar_banco() as connection:
        connection.execute(Path("etl/schema.sql").read_text(encoding="utf-8"))
        seed = not connection.execute("SELECT EXISTS (SELECT 1 FROM pedidos)").fetchone()[0]
    if seed:
        carregar_pedidos()
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, proxy_headers=False)
