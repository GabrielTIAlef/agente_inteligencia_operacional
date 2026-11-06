
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# Definimos uma semente para gerar os mesmos dados
# sempre que executarmos este script.
random.seed(42)

# Pasta onde os arquivos serão salvos.
OUTPUT_DIR = Path(__file__).parent / "synthetic"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REGIOES = [
    "Brasília",
    "São Paulo",
    "Rio de Janeiro",
    "Belo Horizonte",
    "Curitiba",
]

CATEGORIAS = [
    "Restaurante",
    "Mercado",
    "Farmácia",
]

STATUS = [
    "entregue",
    "cancelado",
    "em_atraso",
]

pedidos = []

for pedido_id in range(1, 1001):
    data_pedido = datetime(2026, 10, 1) + timedelta(
        days=random.randint(0, 30)
    )

    pedido = {
        "pedido_id": pedido_id,
        "data_pedido": data_pedido.strftime("%Y-%m-%d"),
        "regiao": random.choice(REGIOES),
        "categoria": random.choice(CATEGORIAS),
        "valor": round(random.uniform(20, 250), 2),
        "status": random.choices(
            STATUS,
            weights=[80, 8, 12],
            k=1,
        )[0],
    }

    pedidos.append(pedido)

arquivo = OUTPUT_DIR / "pedidos.csv"

with arquivo.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=pedidos[0].keys())
    writer.writeheader()
    writer.writerows(pedidos)

print(f"Arquivo gerado: {arquivo}")
print(f"Quantidade de pedidos: {len(pedidos)}")
