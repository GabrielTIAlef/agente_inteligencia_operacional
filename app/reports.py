from datetime import date, datetime, timezone
from app.dashboard import dashboard, OrderStatus

from fastapi import APIRouter, Request

from app.database import get_operations_snapshot

router = APIRouter(prefix="/reports", tags=["Relatórios"])


@router.get("/operations")
def operations_report(request: Request, start: date | None = None, end: date | None = None,
                      region: str | None = None, category: str | None = None,
                      status: OrderStatus | None = None):
    """Gera uma prévia de leitura para o painel e para o n8n."""
    if any(value is not None for value in (start, end, region, category, status)):
        view = dashboard(start, end, region, category, status)

        def metrics(item):
            return {"total_pedidos": item["orders"], "valor_total": item["value"],
                    "taxa_cancelamento": item["cancellation"], "taxa_atraso": item["late"]}

        payload = {
            "summary": metrics(view["summary"]),
            "regions": [{"regiao": item["label"], **metrics(item)} for item in view["regions"]],
            "categories": [{"categoria": item["label"], **metrics(item)} for item in view["categories"]],
            "scope": {"period": view["period"], "region": region, "category": category, "status": status},
            "daily": view["daily"], "previous": view["previous"],
        }
    else:
        # Preserve full-history exports for existing clients (including n8n).
        payload = get_operations_snapshot()
    return {
        "request_id": request.state.request_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "postgresql",
        **payload,
    }
