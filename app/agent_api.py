import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from google.genai.errors import ClientError
from app.agent import perguntar_ao_agente

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agent",
    tags=["AI Agent"],
)


class ChatRequest(BaseModel):
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
    try:
        resposta = perguntar_ao_agente(
            requisicao.message
        )

        return ChatResponse(
            status="success",
            agent="AI Operations Agent",
            response=resposta,
        )


    except ClientError as erro:
        if erro.code == 429:
            logger.warning(
                "Limite de requisições do Gemini atingido."
            )

            raise HTTPException(
                status_code=429,
                detail=(
                    "O limite de uso da IA foi atingido. "
                    "Tente novamente após a renovação da cota."
                ),
            ) from erro

        logger.warning("Erro na API do Gemini (código %s)", erro.code)

        raise HTTPException(
            status_code=502,
            detail="Falha na comunicação com o Gemini.",
        ) from erro

    except Exception as erro:
        logger.error("Erro interno do agente (%s)", type(erro).__name__)

        raise HTTPException(
            status_code=503,
            detail=(
                "O agente não conseguiu processar "
                "a pergunta neste momento."
            ),
        ) from erro
