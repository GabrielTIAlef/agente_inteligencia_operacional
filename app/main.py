from datetime import date
from fastapi import FastAPI, HTTPException, Query
from app.agent_api import router as agent_router
from app.analytics import (
    carregar_pedidos,
    calcular_indicadores,
    calcular_por_regiao,
    calcular_por_categoria,
    filtrar_por_periodo
)

from app.database import (
    get_indicadores_gerais,
    get_indicadores_por_regiao,
    get_indicadores_por_categoria,
    get_regioes_por_periodo,
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


@app.get("/metrics/period")
def get_metrics_by_period(
    start_date: date = Query(
        ...,
        description="Data inicial no formato AAAA-MM-DD"
    ),
    end_date: date = Query(
        ...,
        description="Data final no formato AAAA-MM-DD"
    )
):
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="A data inicial não pode ser posterior à final."
        )

    pedidos = carregar_pedidos()

    pedidos_filtrados = filtrar_por_periodo(
        pedidos,
        start_date,
        end_date
    )

    return {
        "status": "success",
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "data": calcular_indicadores(pedidos_filtrados)
    }


@app.get("/metrics/regions/period")
def get_regions_by_period(
    start_date: date = Query(
        ...,
        description="Data inicial no formato AAAA-MM-DD"
    ),
    end_date: date = Query(
        ...,
        description="Data final no formato AAAA-MM-DD"
    )
):
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="A data inicial não pode ser posterior à final."
        )

    pedidos = carregar_pedidos()

    pedidos_filtrados = filtrar_por_periodo(
        pedidos,
        start_date,
        end_date
    )

    return {
        "status": "success",
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "data": calcular_por_regiao(pedidos_filtrados)
    }


@app.get("/metrics/categories/period")
def get_categories_by_period(
    start_date: date = Query(
        ...,
        description="Data inicial no formato AAAA-MM-DD"
    ),
    end_date: date = Query(
        ...,
        description="Data final no formato AAAA-MM-DD"
    )
):
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="A data inicial não pode ser posterior à final."
        )

    pedidos = carregar_pedidos()

    pedidos_filtrados = filtrar_por_periodo(
        pedidos,
        start_date,
        end_date
    )

    return {
        "status": "success",
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "data": calcular_por_categoria(pedidos_filtrados)
    }


@app.get("/metrics/database")
def get_metrics_database():
    indicadores = get_indicadores_gerais()

    return {
        "status": "success",
        "source": "postgresql",
        "data": indicadores,
    }


@app.get("/metrics/database/regions")
def get_database_regions():
    return {
        "status": "success",
        "source": "postgresql",
        "data": get_indicadores_por_regiao(),
    }


@app.get("/metrics/database/categories")
def get_database_categories():
    return {
        "status": "success",
        "source": "postgresql",
        "data": get_indicadores_por_categoria(),
    }


@app.get("/metrics/database/regions/period")
def get_database_regions_by_period(
    start_date: date,
    end_date: date,
):
    if start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="A data inicial não pode ser posterior à final.",
        )

    return {
        "status": "success",
        "source": "postgresql",
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
        "data": get_regioes_por_periodo(
            start_date,
            end_date,
        ),
    }

app.include_router(agent_router)
