
from fastapi import FastAPI

from app.analytics import (
    carregar_pedidos,
    calcular_indicadores,
    calcular_por_regiao,
    calcular_por_categoria,
)

app = FastAPI(
    title="AI Operations Agent",
    description="API de inteligência operacional para um marketplace fictício.",
    version="0.2.0",
)


@app.get("/")
def home():
    return {
        "message": "Bem-vindo ao AI Operations Agent",
        "version": "0.2.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ai-operations-agent",
    }


@app.get("/metrics")
def get_metrics():
    pedidos = carregar_pedidos()
    indicadores = calcular_indicadores(pedidos)

    return {
        "status": "success",
        "data": indicadores,
    }


@app.get("/metrics/regions")
def get_metrics_by_region():
    pedidos = carregar_pedidos()

    return {
        "status": "success",
        "data": calcular_por_regiao(pedidos)
    }


@app.get("/metrics/categories")
def get_metrics_by_category():
    pedidos = carregar_pedidos()

    return {
        "status": "success",
        "data": calcular_por_categoria(pedidos)
    }
