"""Indicadores do painel sobre um recorte consistente do PostgreSQL."""
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, HTTPException

from etl.load_orders import conectar_banco

router = APIRouter()


def summarize(rows):
    count = len(rows)
    status = Counter(row[4] for row in rows)
    value = sum((row[3] for row in rows), Decimal(0))
    return {
        "orders": count,
        "value": float(value),
        "average": round(float(value / count), 2) if count else None,
        "status": {key: status[key] for key in ("entregue", "cancelado", "em_atraso")},
        "cancellation": 100 * status["cancelado"] / count if count else None,
        "late": 100 * status["em_atraso"] / count if count else None,
    }


def group(rows, index):
    groups = defaultdict(list)
    for row in rows:
        groups[row[index]].append(row)
    return [{"label": str(label), **summarize(group_rows)}
            for label, group_rows in sorted(groups.items())]


def snapshot(connection, start=None, end=None, region=None, category=None, days=30):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT min(data_pedido), max(data_pedido),
                   array_agg(DISTINCT regiao ORDER BY regiao),
                   array_agg(DISTINCT categoria ORDER BY categoria)
            FROM pedidos
        """)
        first, latest, regions, categories = cursor.fetchone()
        filters = {"regions": regions or [], "categories": categories or []}
        if latest is None and end is None:
            return {"coverage": None, "period": None, "filters": filters,
                    "summary": summarize([]), "previous": None, "daily": [],
                    "regions": [], "categories": []}
        end = end or latest
        start = start or end - timedelta(days=days - 1)
        span = (end - start).days + 1
        if not 1 <= span <= 366:
            raise HTTPException(422, "Escolha um intervalo de 1 a 366 dias.")
        previous_start = start - timedelta(days=span)
        cursor.execute("""
            SELECT data_pedido, regiao, categoria, valor, status FROM pedidos
            WHERE data_pedido BETWEEN %s AND %s
              AND (%s::text IS NULL OR regiao = %s)
              AND (%s::text IS NULL OR categoria = %s)
        """, (previous_start, end, region, region, category, category))
        rows = cursor.fetchall()
    current = [row for row in rows if row[0] >= start]
    daily = {item["label"]: item["orders"] for item in group(current, 0)}
    comparable = first is not None and previous_start >= first and end <= latest
    return {
        "coverage": {"start": first, "end": latest} if latest else None,
        "period": {"start": start, "end": end},
        "filters": filters,
        "summary": summarize(current),
        "previous": summarize([row for row in rows if row[0] < start]) if comparable else None,
        "daily": [{"date": day, "orders": daily.get(str(day), 0)}
                  for offset in range(span) if first is not None
                  and first <= (day := start + timedelta(days=offset)) <= latest],
        "regions": sorted(group(current, 1), key=lambda item: -item["orders"]),
        "categories": sorted(group(current, 2), key=lambda item: -item["orders"]),
    }


@router.get("/operations/dashboard")
def dashboard(start: date | None = None, end: date | None = None,
              region: str | None = None, category: str | None = None):
    if bool(start) != bool(end) or (start and not 1 <= (end - start).days + 1 <= 366):
        raise HTTPException(422, "Informe as duas datas em um intervalo de 1 a 366 dias.")
    if start and start.year < 1900:
        raise HTTPException(422, "Informe uma data a partir de 1900.")
    with conectar_banco(somente_leitura=True) as connection:
        connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        return snapshot(connection, start, end, region, category)
