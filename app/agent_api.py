import logging
import os
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from google.genai.errors import ClientError
from app.access import trace_id
from app.agent import perguntar_ao_agente
from app.chat_quota import reserve_request

logger = logging.getLogger("uvicorn.error")

router = APIRouter(
    prefix="/agent",
    tags=["AI Agent"],
)


class ContextMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str = Field(min_length=1, max_length=1500)


class ChatRequest(BaseModel):
    history: list[ContextMessage] = Field(default_factory=list, max_length=6)

    message: str = Field(
        min_length=1,
        max_length=500,
    )

    @field_validator("message")
    @classmethod
    def validar_mensagem(cls, valor: str) -> str:
        valor = valor.strip()

        if not valor:
            raise ValueError(
                "A mensagem não pode estar vazia."
            )

        return valor


class ChatResponse(BaseModel):
    status: str
    agent: str
    response: str


@router.post("/chat", response_model=ChatResponse)
def conversar_com_agente(requisicao: ChatRequest):
    if os.getenv("APP_PUBLIC_DEPLOYMENT") == "true" and (
        os.getenv("GEMINI_FREE_TIER_CONFIRMED") != "true"
        or not os.getenv("GEMINI_API_KEY")
    ):
        raise HTTPException(503, "Chat desativado até confirmar acesso gratuito ao Gemini.")
    if os.getenv("APP_PUBLIC_DEPLOYMENT") == "true" and not reserve_request():
        raise HTTPException(429, "Limite diário da demonstração atingido.")
    try:
        if requisicao.history:
            resposta = perguntar_ao_agente(
                requisicao.message,
                history=[item.model_dump() for item in requisicao.history],
            )
        else:
            resposta = perguntar_ao_agente(requisicao.message)

        return ChatResponse(
            status="success",
            agent="AI Operations Agent",
            response=resposta,
        )


    except ClientError as erro:
        if erro.code == 429:
            logger.warning(
                "request_id=%s gemini_status=429", trace_id.get()
            )

            raise HTTPException(
                status_code=429,
                detail=(
                    "O limite de uso da IA foi atingido. "
                    "Tente novamente após a renovação da cota."
                ),
            ) from erro

        logger.warning("request_id=%s gemini_status=%s", trace_id.get(), erro.code)

        raise HTTPException(
            status_code=502,
            detail="Falha na comunicação com o Gemini.",
        ) from erro

    except Exception as erro:
        logger.error("request_id=%s agent_error=%s", trace_id.get(), type(erro).__name__)

        raise HTTPException(
            status_code=503,
            detail=(
                "O agente não conseguiu processar "
                "a pergunta neste momento."
            ),
        ) from erro
