"""Execução idempotente e histórico do monitor operacional."""
import hmac
import json
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Header, HTTPException
from fastapi.encoders import jsonable_encoder
from google import genai
from google.genai import types
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.dashboard import snapshot
from etl.load_orders import conectar_banco

router = APIRouter(prefix="/operations/monitor")
logger = logging.getLogger("uvicorn.error")


def detect(report):
    current, previous = report["summary"], report["previous"]
    alerts = []
    for key, label, threshold in (("cancellation", "Cancelamento", 10), ("late", "Atraso", 15)):
        if current["orders"] >= 30 and current[key] >= threshold:
            alerts.append({"label": label, "value": round(current[key], 2),
                           "threshold": threshold, "unit": "%", "sample": current["orders"]})
    if previous and previous["orders"] >= 30:
        drop = 100 * (previous["orders"] - current["orders"]) / previous["orders"]
        if drop >= 30:
            alerts.append({"label": "Queda no volume", "value": round(drop, 2),
                           "threshold": 30, "unit": "%", "sample": previous["orders"]})
    return alerts


def narrative(report, alerts):
    count = report["summary"]["orders"]
    fallback = (f"{count} pedidos na janela de análise. "
                f"{len(alerts)} regras atingiram seus limiares."
                if count else "Nenhum pedido na janela de análise.")
    key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("MONITOR_GEMINI_MODEL")
    if not (alerts and key and model and os.getenv("MONITOR_GEMINI_ENABLED") == "true"):
        return fallback, "determinístico"
    try:
        with genai.Client(api_key=key, http_options=types.HttpOptions(
            timeout=5000, retry_options=types.HttpRetryOptions(attempts=1)
        )) as client:
            response = client.models.generate_content(
                model=model,
                contents="Resuma em português os indicadores agregados abaixo em até 3 frases. "
                         "Não invente causas ou valores. " + json.dumps({"pedidos": count, "alertas": alerts}),
                config=types.GenerateContentConfig(max_output_tokens=400),
            )
            if response.text and response.text.strip():
                return response.text.strip()[:1200], "gemini"
    except Exception as error:
        logger.warning("monitor_gemini_fallback=%s", type(error).__name__)
    return fallback, "fallback"


@router.post("/run")
def run_monitor(authorization: str = Header(default="")):
    secret = os.getenv("MONITOR_TOKEN")
    if not secret or not hmac.compare_digest(authorization.encode(), f"Bearer {secret}".encode()):
        raise HTTPException(403, "Credencial do monitor inválida.")
    slot = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    with conectar_banco() as connection:
        connection.execute("SET LOCAL statement_timeout = '10s'")
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s, %s)", (7204, slot.toordinal()))
            cursor.execute("SELECT * FROM monitor_runs WHERE slot = %s AND status = 'completed'", (slot,))
            existing = cursor.fetchone()
            if existing:
                return existing
            try:
                with connection.transaction():
                    connection.execute("LOCK TABLE pedidos IN SHARE MODE")
                    report = snapshot(connection, days=14)
                    alerts = detect(report)
                    summary, method = narrative(report, alerts)
                    payload = Jsonb(jsonable_encoder({
                        "period": report["period"], "metrics": report["summary"],
                        "previous": report["previous"], "alerts": alerts,
                        "summary": summary, "method": method,
                        "notification_candidate": bool(alerts) and os.getenv("MONITOR_NOTIFICATION_MODE") == "preview",
                    }))
            except Exception as error:
                logger.warning("monitor_run_failed=%s", type(error).__name__)
                cursor.execute("""
                    INSERT INTO monitor_runs(slot, status) VALUES (%s, 'failed')
                """, (slot,))
            else:
                cursor.execute("""
                    INSERT INTO monitor_runs(slot, status, report)
                    VALUES (%s, 'completed', %s) RETURNING *
                """, (slot, payload))
                return cursor.fetchone()
    raise HTTPException(503, "Falha ao gerar o monitoramento. Consulte o histórico.")


@router.get("/runs")
def monitor_runs():
    with conectar_banco(somente_leitura=True) as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SELECT * FROM monitor_runs ORDER BY id DESC LIMIT 20")
            return {"runs": cursor.fetchall()}

