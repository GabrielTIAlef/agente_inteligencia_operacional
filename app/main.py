
from fastapi import FastAPI

app = FastAPI(
    title="AI Operations Agent",
    description="API de inteligência operacional para um marketplace fictício.",
    version="0.1.0"
)


@app.get("/")
def home():
    return {
        "message": "Bem-vindo ao AI Operations Agent",
        "version": "0.1.0"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ai-operations-agent"
    }
