from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.database import get_operations_snapshot

router = APIRouter(prefix="/reports", tags=["Relatórios"])


@router.get("/operations")
def operations_report(request: Request):
    """Gera uma prévia de leitura para o painel e para o n8n."""
    return {
        "request_id": request.state.request_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "postgresql",
        **get_operations_snapshot(),
    }
